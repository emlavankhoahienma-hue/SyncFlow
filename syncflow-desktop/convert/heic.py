from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger("syncflow.convert.heic")

def convert_heic_to_png(input_path: Path, output_path: Optional[Path] = None) -> Tuple[bool, Path, str]:
    """
    Converts a HEIC/HEIF image to PNG while preserving quality and color depth.
    Uses pillow_heif and Pillow.
    """
    try:
        from PIL import Image
        import pillow_heif

        pillow_heif.register_heif_opener()

        if output_path is None:
            output_path = input_path.with_suffix(".png")

        with Image.open(input_path) as image:
            # Preserve color profile / exif if available
            exif = image.info.get("exif")
            icc_profile = image.info.get("icc_profile")

            save_kwargs = {"format": "PNG"}
            if exif:
                save_kwargs["exif"] = exif
            if icc_profile:
                save_kwargs["icc_profile"] = icc_profile

            image.save(output_path, **save_kwargs)

        logger.info(f"Successfully converted {input_path} to {output_path}")
        return True, output_path, "Conversion succeeded"
    except Exception as e:
        logger.error(f"Failed to convert HEIC to PNG: {e}")
        return False, input_path, str(e)
