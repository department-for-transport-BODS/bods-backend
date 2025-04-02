"""
Script to split a zip of XMLs into smaller chunks
"""

import lzma
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Annotated

import typer
from pydantic import BaseModel
from structlog.stdlib import get_logger

log = get_logger()


class FileInfo(BaseModel):
    """
    File information
    """

    name: str
    size: int
    compressed_size: int
    compression_type: int
    estimated_lzma_size: int | None


def get_xml_files_info(source_zip_path: str | Path) -> list[FileInfo]:
    """
    Extract information about all XML files in the source zip,
    including their compression details.
    """
    xml_files: list[FileInfo] = []

    with zipfile.ZipFile(source_zip_path, "r") as zip_ref:
        for info in zip_ref.infolist():
            if info.filename.lower().endswith(".xml"):
                xml_files.append(
                    FileInfo(
                        name=info.filename,
                        size=info.file_size,
                        compressed_size=info.compress_size,
                        compression_type=info.compress_type,
                        estimated_lzma_size=None,
                    )
                )

    compression_types = {f.compression_type for f in xml_files}
    compression_methods = {
        zipfile.ZIP_STORED: "no compression",
        zipfile.ZIP_DEFLATED: "deflated",
        zipfile.ZIP_BZIP2: "bzip2",
        zipfile.ZIP_LZMA: "LZMA",
    }

    compression_info = [
        f"{compression_methods.get(ct, f'unknown ({ct})')}: "
        f"{sum(1 for f in xml_files if f.compression_type == ct)} files"
        for ct in compression_types
    ]

    log.info(
        "Found XML files in source zip",
        count=len(xml_files),
        compression_types=", ".join(compression_info),
    )

    return xml_files


def estimate_lzma_size(
    source_zip_path: str | Path,
    file_info: FileInfo,
    lzma_preset: int = 6,
    sample_size: int = 100000,
) -> FileInfo:
    """
    Estimate LZMA compressed size if the file isn't already LZMA compressed.
    For LZMA compressed files, use the existing size as a good approximation.
    """

    updated_info = file_info.model_copy()

    # If already LZMA compressed, use that size as a good estimate
    if file_info.compression_type == zipfile.ZIP_LZMA:
        updated_info.estimated_lzma_size = file_info.compressed_size
        log.info(
            "Using existing LZMA size",
            filename=file_info.name,
            compressed_size=file_info.compressed_size,
        )
        return updated_info

    # For non-LZMA files, estimate the compression
    try:
        with zipfile.ZipFile(source_zip_path, "r") as zip_ref:
            # For large files, only compress a sample to estimate ratio
            if sample_size > 0 and file_info.size > sample_size * 2:
                content = zip_ref.read(file_info.name)[:sample_size]
                sample_compressed_size = len(lzma.compress(content, preset=lzma_preset))
                ratio = sample_compressed_size / len(content)
                estimated_lzma_size = int(ratio * file_info.size)
            else:
                # For smaller files, compress the entire file
                content = zip_ref.read(file_info.name)
                estimated_lzma_size = len(lzma.compress(content, preset=lzma_preset))

            updated_info.estimated_lzma_size = estimated_lzma_size

            log.info(
                "Estimated LZMA compression",
                filename=file_info.name,
                original_size=file_info.size,
                current_compression=file_info.compression_type,
                estimated_lzma_size=estimated_lzma_size,
            )
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Fallback to a reasonable estimate based on original compressed size
        log.error(
            "Error estimating LZMA compression",
            filename=file_info.name,
            error=str(e),
        )

        # If we have some compressed size already, use it as a basis
        if file_info.compressed_size > 0:
            # Add 20% buffer for potential differences between compression algorithms
            updated_info.estimated_lzma_size = int(file_info.compressed_size * 1.2)
        else:
            # Assume 10:1 compression ratio as fallback
            updated_info.estimated_lzma_size = int(file_info.size * 0.1)

    return updated_info


def process_files_in_parallel(
    source_zip_path: str | Path,
    file_infos: list[FileInfo],
    lzma_preset: int = 6,
    sample_size: int = 100000,
    max_workers: int = 8,
) -> list[FileInfo]:
    """Process files in parallel to estimate LZMA sizes if needed."""

    # Skip estimation if all files are already LZMA compressed
    if all(f.compression_type == zipfile.ZIP_LZMA for f in file_infos):
        log.info("All files already LZMA compressed, skipping estimation")
        for f in file_infos:
            f.estimated_lzma_size = f.compressed_size
        return file_infos

    # Process only non-LZMA files or if requested
    files_to_process = [f for f in file_infos if f.compression_type != zipfile.ZIP_LZMA]

    if not files_to_process:
        return file_infos

    log.info("Estimating LZMA size for non-LZMA files", count=len(files_to_process))

    estimate_func = partial(
        estimate_lzma_size,
        source_zip_path,
        lzma_preset=lzma_preset,
        sample_size=sample_size,
    )

    updated_infos: list[FileInfo] = [
        f for f in file_infos if f.compression_type == zipfile.ZIP_LZMA
    ]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(estimate_func, file_info): file_info
            for file_info in files_to_process
        }

        for future in as_completed(future_to_file):
            updated_info = future.result()
            updated_infos.append(updated_info)

    return updated_infos


def estimate_zip_overhead(file_infos: list[FileInfo]) -> float:
    """

    Estimate overhead using the central directory size formula
    Each file entry in the central directory is approximately 46 bytes
    plus the length of the filename
    """

    estimated_overhead = 0

    # Fixed zip overhead (end of central directory)
    estimated_overhead += 22

    # Per-file overhead
    for file_info in file_infos:
        # Central directory entry (fixed + filename length)
        estimated_overhead += 46 + len(file_info.name)

        # Local file header (fixed + filename length)
        estimated_overhead += 30 + len(file_info.name)

    overhead_per_file = estimated_overhead / len(file_infos) if file_infos else 100

    log.debug(
        "Estimated zip overhead",
        total_overhead=estimated_overhead,
        overhead_per_file=overhead_per_file,
        files_count=len(file_infos),
    )

    return overhead_per_file


def select_files_for_target_size(
    file_infos: list[FileInfo],
    target_size_bytes: int,
    overhead_per_file: float,
    max_files: int = 10000,
) -> list[FileInfo]:
    """Select files to maximize count while staying under target size and file count limit."""

    # Verify all files have estimated LZMA size
    valid_files = [f for f in file_infos if f.estimated_lzma_size is not None]

    # Sort by estimated LZMA size (smallest first)
    sorted_files = sorted(
        valid_files,
        key=lambda x: x.estimated_lzma_size if x.estimated_lzma_size is not None else 0,
    )

    total_size = 0
    included_files: list[FileInfo] = []

    for file_info in sorted_files:
        if file_info.estimated_lzma_size is None:
            log.error(
                "File Info Estimated LZMA Size is None, skipping", file_info=file_info
            )
            continue
        # Check if we've reached the maximum number of files
        if len(included_files) >= max_files:
            log.info("Reached maximum file count limit", max_files=max_files)
            break

        file_contribution = file_info.estimated_lzma_size + overhead_per_file
        new_size = total_size + file_contribution

        if new_size <= target_size_bytes:
            included_files.append(file_info)
            total_size = new_size
        else:
            # Stop when we reach the target size
            break

    log.info(
        "Selected files to include",
        files_count=len(included_files),
        estimated_size=total_size,
        target_size=target_size_bytes,
        max_files=max_files,
        utilization_percentage=(
            (total_size / target_size_bytes) * 100 if target_size_bytes > 0 else 0
        ),
    )

    return included_files


def create_lzma_zip(
    source_zip_path: str | Path,
    output_path: str | Path,
    files_to_include: list[FileInfo],
    chunk_size: int = 1024 * 1024,  # 1MB chunks
) -> int:
    """Create a new LZMA-compressed zip with selected files."""

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_LZMA) as output_zip:
        with zipfile.ZipFile(source_zip_path, "r") as source_zip:
            for idx, file_info in enumerate(files_to_include):
                # For larger files, use chunking to avoid memory issues
                if file_info.size > chunk_size * 5:
                    log.info(
                        "Adding large file with chunking",
                        filename=file_info.name,
                        size=file_info.size,
                        progress=f"{idx+1}/{len(files_to_include)}",
                    )

                    with source_zip.open(file_info.name) as source_file:
                        with output_zip.open(file_info.name, "w") as target_file:
                            while True:
                                chunk = source_file.read(chunk_size)
                                if not chunk:
                                    break
                                target_file.write(chunk)
                else:
                    log.info(
                        "Adding file",
                        filename=file_info.name,
                        size=file_info.size,
                        progress=f"{idx+1}/{len(files_to_include)}",
                    )
                    output_zip.writestr(file_info.name, source_zip.read(file_info.name))

    final_size = os.path.getsize(output_path)

    log.info(
        "Created LZMA zip", files_included=len(files_to_include), final_size=final_size
    )

    return final_size


def batch_optimize_xml_zip(
    source_zip_path: str | Path,
    output_folder: str | Path,
    target_size_bytes: int,
    lzma_preset: int = 6,
    max_workers: int = 8,
    max_files_per_zip: int = 10000,
) -> list[tuple[str, int]]:
    """
    Create multiple zip files with LZMA compression, each maximizing
    the number of XML files while staying under the target size.


    Returns:
        list: List of tuples containing (zip_filename, size_in_bytes)
    """
    # Step 1: Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Step 2: Get information about all XML files
    all_xml_files = get_xml_files_info(source_zip_path)

    if not all_xml_files:
        log.warning("No XML files found in source zip")
        return []

    # Step 3: Process files to get estimated LZMA sizes
    processed_files = process_files_in_parallel(
        source_zip_path, all_xml_files, lzma_preset, max_workers=max_workers
    )

    # Step 4: Estimate zip overhead
    overhead_per_file = estimate_zip_overhead(processed_files)

    # Step 5: Create zips until all files are included
    remaining_files = processed_files.copy()
    created_zips: list[tuple[str, int]] = []
    zip_index: int = 1

    while remaining_files:
        # Create output zip path
        output_zip_path = os.path.join(
            output_folder, f"all_fares_part_{zip_index:03d}.zip"
        )

        # Select files for this zip
        files_to_include = select_files_for_target_size(
            remaining_files, target_size_bytes, overhead_per_file, max_files_per_zip
        )

        if not files_to_include:
            log.warning("Could not fit any remaining files in a new zip")
            break

        # Create the zip
        final_size = create_lzma_zip(source_zip_path, output_zip_path, files_to_include)

        # Add to the list of created zips
        created_zips.append((output_zip_path, final_size))

        # Remove included files from remaining files
        included_filenames = {file_info.name for file_info in files_to_include}
        remaining_files = [
            file_info
            for file_info in remaining_files
            if file_info.name not in included_filenames
        ]

        log.info(
            "Created zip batch",
            zip_index=zip_index,
            zip_path=output_zip_path,
            size_bytes=final_size,
            size_mb=final_size / (1024 * 1024),
            files_included=len(files_to_include),
            max_files_per_zip=max_files_per_zip,
            remaining_files=len(remaining_files),
        )

        zip_index += 1

    return created_zips


def multi_zip_maker(
    input_zip: Path,
    output_folder: Path,
    target_size_mb: int = 30,
    max_files_per_zip: int = 5000,
):
    """
    Split a ZIP of XML files into multiple Zips
    """
    start_time = datetime.now()
    target_size_bytes = target_size_mb * 1024 * 1024
    log.info(
        "Starting batch XML zip optimization",
        input_file=input_zip,
        output_folder=output_folder,
        target_size_mb=target_size_mb,
        target_size_bytes=target_size_bytes,
    )
    # Check if input file exists
    if not os.path.exists(input_zip):
        log.error("Input file does not exist", path=input_zip)
        return

    input_size = os.path.getsize(input_zip)
    log.info(
        "Input zip information",
        size_bytes=input_size,
        size_mb=input_size / (1024 * 1024),
    )

    try:

        created_zips = batch_optimize_xml_zip(
            source_zip_path=input_zip,
            output_folder=output_folder,
            target_size_bytes=target_size_bytes,
            lzma_preset=6,
            max_workers=8,
            max_files_per_zip=max_files_per_zip,
        )

        elapsed_time = (datetime.now() - start_time).total_seconds()

        total_size = sum(size for _, size in created_zips)

        log.info(
            "Batch optimization complete",
            elapsed_seconds=elapsed_time,
            zips_created=len(created_zips),
            total_output_size_bytes=total_size,
            total_output_size_mb=total_size / (1024 * 1024),
        )

        # Log details about each created zip
        for i, (zip_path, size) in enumerate(created_zips, 1):
            zip_name = os.path.basename(zip_path)
            log.info(
                "Zip information",
                zip_number=i,
                zip_name=zip_name,
                size_bytes=size,
                size_mb=size / (1024 * 1024),
            )

    except Exception as e:  # pylint: disable=broad-exception-caught
        log.error("Error during optimization", error=str(e), exc_info=True)


def multi_zip(
    input_zip: Annotated[
        Path, typer.Argument(help="Path to the input zip file")
    ] = Path("data/fares/bodds_fares_archive_20250331-no-sub-zips-no-whitespace.zip"),
    output_folder: Annotated[
        Path, typer.Argument(help="Path to the output folder for batched zip files")
    ] = Path("fares_batched_zips_30"),
    target_size_mb: Annotated[
        int, typer.Option(help="Target size for each output zip file in MB")
    ] = 30,
    max_files_per_zip: Annotated[
        int, typer.Option(help="Maximum number of files per output zip")
    ] = 5000,
) -> None:
    """
    Create multiple zip files from a single input zip,
    targeting specific size and file count limits.
    """

    log.info(
        "Starting multi-zip process",
        input_zip=input_zip,
        output_folder=output_folder,
        target_size_mb=target_size_mb,
        max_files_per_zip=max_files_per_zip,
    )

    multi_zip_maker(input_zip, output_folder, target_size_mb, max_files_per_zip)

    log.info("Multi-zip process complete", output_folder=output_folder)


if __name__ == "__main__":
    typer.run(multi_zip)
