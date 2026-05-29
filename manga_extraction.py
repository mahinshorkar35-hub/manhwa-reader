"""
Manga Extraction Module
Handles PDF page extraction, panel detection, and image preprocessing.
"""

import os
import cv2
import numpy as np
import fitz  # PyMuPDF
from PIL import Image
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class MangaExtractor:
    """Extracts and processes manga pages from PDF files."""

    def __init__(self, extraction_level: str = "medium"):
        """
        Initialize the manga extractor.

        Args:
            extraction_level: Panel detection sensitivity - "low", "medium", or "high"
        """
        self.extraction_level = extraction_level
        self.sensitivity_map = {
            "low": {"min_area_ratio": 0.15, "padding": 10},
            "medium": {"min_area_ratio": 0.08, "padding": 15},
            "high": {"min_area_ratio": 0.03, "padding": 20}
        }
        self.settings = self.sensitivity_map.get(extraction_level, self.sensitivity_map["medium"])

    def extract_pages(
        self,
        pdf_path: str,
        output_dir: str,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> List[str]:
        """
        Extract all pages from a PDF as images.

        Args:
            pdf_path: Path to the manga PDF file
            output_dir: Directory to save extracted page images
            progress_callback: Optional callback(page_info, progress_percent)

        Returns:
            List of paths to extracted page images
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        logger.info(f"Opening PDF: {pdf_path}")
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        logger.info(f"Total pages: {total_pages}")

        page_images = []

        for page_num in range(total_pages):
            page = doc[page_num]

            # Render at 2x resolution for quality
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)

            image_path = output_dir / f"page_{page_num:04d}.png"
            pix.save(str(image_path))
            page_images.append(str(image_path))

            if progress_callback:
                progress = int((page_num + 1) / total_pages * 100)
                progress_callback(f"Extracting page {page_num + 1}/{total_pages}", progress)

            logger.debug(f"Extracted page {page_num + 1}: {image_path}")

        doc.close()
        logger.info(f"Extracted {len(page_images)} pages to {output_dir}")
        return page_images

    def detect_panels(
        self,
        page_image: str,
        output_dir: Optional[str] = None
    ) -> List[Dict]:
        """
        Detect manga panels in a page image using computer vision.

        Args:
            page_image: Path to the page image
            output_dir: Optional directory to save panel crops

        Returns:
            List of panel dictionaries with 'bbox', 'image_path', and 'coords'
        """
        image = cv2.imread(page_image)
        if image is None:
            logger.error(f"Could not load image: {page_image}")
            return []

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        # Apply adaptive thresholding to find panel boundaries
        # Manga panels are typically separated by white/black lines
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Find contours that represent panel boundaries
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        panels = []
        min_area = (width * height) * self.settings["min_area_ratio"]
        padding = self.settings["padding"]

        for idx, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h

            if area < min_area:
                continue

            # Apply padding and clamp to image bounds
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(width, x + w + padding)
            y2 = min(height, y + h + padding)

            panel = {
                'bbox': (x1, y1, x2, y2),
                'coords': {
                    'x': x1,
                    'y': y1,
                    'width': x2 - x1,
                    'height': y2 - y1
                },
                'area': area,
                'image_path': None
            }
            panels.append(panel)

        # Sort panels by reading order (top-to-bottom, left-to-right for manga)
        panels.sort(key=lambda p: (p['bbox'][1], p['bbox'][0]))

        # Save panel crops if output directory is provided
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            page_name = Path(page_image).stem

            for idx, panel in enumerate(panels):
                x1, y1, x2, y2 = panel['bbox']
                panel_img = image[y1:y2, x1:x2]
                panel_path = output_dir / f"{page_name}_panel_{idx:03d}.png"
                cv2.imwrite(str(panel_path), panel_img)
                panel['image_path'] = str(panel_path)

        logger.info(f"Detected {len(panels)} panels in {page_image}")
        return panels

    def extract_all_panels(
        self,
        page_images: List[str],
        output_dir: str,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> List[List[Dict]]:
        """
        Detect panels in all extracted pages.

        Args:
            page_images: List of page image paths
            output_dir: Directory to save panel images
            progress_callback: Optional callback(info, progress_percent)

        Returns:
            List of panel lists for each page
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        all_panels = []
        total = len(page_images)

        for i, page_image in enumerate(page_images):
            panels = self.detect_panels(page_image, str(output_dir / "panels"))
            all_panels.append(panels)

            if progress_callback:
                progress = int((i + 1) / total * 100)
                progress_callback(f"Analyzing page {i + 1}/{total} panels", progress)

        return all_panels

    def get_page_preview(self, page_image: str, max_size: Tuple[int, int] = (400, 400)) -> Image.Image:
        """
        Get a resized preview of a page for GUI display.

        Args:
            page_image: Path to page image
            max_size: Maximum dimensions for preview

        Returns:
            Resized PIL Image
        """
        img = Image.open(page_image)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        return img

    def detect_manga_metadata(self, pdf_path: str) -> Dict:
        """
        Attempt to detect manga title and volume from PDF metadata or filename.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with 'title', 'volume', and other metadata
        """
        pdf_path = Path(pdf_path)
        metadata = {
            'title': '',
            'volume': '',
            'author': '',
            'total_pages': 0
        }

        # Try to get metadata from PDF
        try:
            doc = fitz.open(str(pdf_path))
            pdf_metadata = doc.metadata

            if pdf_metadata.get('title'):
                metadata['title'] = pdf_metadata['title']
            if pdf_metadata.get('author'):
                metadata['author'] = pdf_metadata['author']

            metadata['total_pages'] = len(doc)
            doc.close()
        except Exception as e:
            logger.warning(f"Could not extract PDF metadata: {e}")

        # Try to parse filename for title/volume info
        if not metadata['title']:
            filename = pdf_path.stem
            # Common patterns: "Manga_Title_Vol_1", "Title - Volume 01", etc.
            import re

            # Try to extract volume number
            vol_patterns = [
                r'[Vv]ol[.\s]*(\d+)',
                r'[Vv]olume[.\s]*(\d+)',
                r'[Vv]\s*(\d+)',
                r'\b(\d+)\s*$'
            ]

            for pattern in vol_patterns:
                match = re.search(pattern, filename)
                if match:
                    metadata['volume'] = match.group(1)
                    # Remove volume info from title
                    title = re.sub(pattern, '', filename).strip()
                    title = re.sub(r'[_-]', ' ', title).strip()
                    metadata['title'] = title
                    break

            if not metadata['title']:
                metadata['title'] = filename.replace('_', ' ').replace('-', ' ').strip()

        return metadata

    def cleanup(self, output_dir: str):
        """
        Clean up temporary extraction files.

        Args:
            output_dir: Directory to clean up
        """
        import shutil
        output_dir = Path(output_dir)
        if output_dir.exists():
            shutil.rmtree(output_dir)
            logger.info(f"Cleaned up: {output_dir}")
