from paddleocr import PaddleOCR
from typing import Dict, Any, Optional
import io
from PIL import Image
import pdf2image
import numpy as np
import time
import logging

# Import network error types - handle both http.client and urllib3 sources
_network_errors = []

# http.client.IncompleteRead (Python standard library)
try:
    from http.client import IncompleteRead
    _network_errors.append(IncompleteRead)
except ImportError:
    pass

# urllib3 exceptions
try:
    from urllib3.exceptions import IncompleteRead as URLLib3IncompleteRead, ProtocolError
    _network_errors.append(URLLib3IncompleteRead)
    _network_errors.append(ProtocolError)
except ImportError:
    pass

# requests exceptions
try:
    from requests.exceptions import ConnectionError as RequestsConnectionError, Timeout as RequestsTimeout
    _network_errors.append(RequestsConnectionError)
    _network_errors.append(RequestsTimeout)
except ImportError:
    pass

# Create tuple for exception handling (fallback to Exception if none found)
NetworkErrors = tuple(_network_errors) if _network_errors else (Exception,)

logger = logging.getLogger(__name__)

class OCRService:
    _instance: Optional[PaddleOCR] = None
    _initialization_lock = False
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 5):
        """
        Initialize OCRService with retry logic for model downloads.
        
        Args:
            max_retries: Maximum number of retries for PaddleOCR initialization
            retry_delay: Delay in seconds between retries
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.ocr = self._initialize_ocr()
    
    def _initialize_ocr(self) -> PaddleOCR:
        """Initialize PaddleOCR with retry logic for network errors"""
        # Use singleton pattern to avoid re-downloading models
        if OCRService._instance is not None:
            return OCRService._instance
        
        # Prevent concurrent initialization
        if OCRService._initialization_lock:
            logger.warning("PaddleOCR initialization already in progress, waiting...")
            time.sleep(self.retry_delay)
            if OCRService._instance is not None:
                return OCRService._instance
        
        OCRService._initialization_lock = True
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Initializing PaddleOCR (attempt {attempt}/{self.max_retries})...")
                ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='en',
                    use_gpu=False,
                    show_log=False  # Reduce verbose output
                )
                OCRService._instance = ocr
                OCRService._initialization_lock = False
                logger.info("PaddleOCR initialized successfully")
                return ocr
            except NetworkErrors as e:
                logger.warning(f"Network error during PaddleOCR initialization (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to initialize PaddleOCR after {self.max_retries} attempts")
                    OCRService._initialization_lock = False
                    raise Exception(f"Failed to initialize PaddleOCR after {self.max_retries} attempts: {e}")
            except Exception as e:
                logger.error(f"Unexpected error during PaddleOCR initialization: {e}")
                OCRService._initialization_lock = False
                raise
        
        OCRService._initialization_lock = False
        raise Exception("Failed to initialize PaddleOCR")
    
    def extract_text(self, file_data: bytes, mime_type: str) -> Dict[str, Any]:
        """Extract text from document using OCR"""
        try:
            # Convert to image if needed
            if mime_type == "application/pdf":
                images = pdf2image.convert_from_bytes(file_data)
                image = images[0]  # Process first page
                image_np = np.array(image)
            else:
                image = Image.open(io.BytesIO(file_data))
                image_np = np.array(image)
            
            # Run OCR
            result = self.ocr.ocr(image_np, cls=True)
            
            # Extract text and calculate confidence
            text_lines = []
            all_text = []
            total_confidence = 0.0
            confidence_count = 0
            
            if result and result[0]:
                for line in result[0]:
                    if line:
                        text_info = line[1]
                        text = text_info[0]
                        confidence = text_info[1]
                        
                        text_lines.append({
                            "text": text,
                            "confidence": confidence,
                            "bbox": line[0] if len(line) > 0 else None
                        })
                        all_text.append(text)
                        total_confidence += confidence
                        confidence_count += 1
            
            full_text = " ".join(all_text)
            avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0.0
            
            return {
                "text": full_text,
                "confidence": avg_confidence,
                "detailed_results": {
                    "lines": text_lines,
                    "line_count": len(text_lines)
                }
            }
        except NetworkErrors as e:
            logger.error(f"Network error during OCR processing: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "detailed_results": {
                    "error": f"Network error during OCR processing: {str(e)}",
                    "error_type": "network_error"
                }
            }
        except Exception as e:
            logger.error(f"OCR Error: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "detailed_results": {
                    "error": str(e),
                    "error_type": "ocr_error"
                }
            }

