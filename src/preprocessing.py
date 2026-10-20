import cv2
import numpy as np

def preprocess_image(image):
    # Renkli görüntüyü Gri Tonlamaya dönüştür
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Gürültüyü azaltmak için Gaussian Blur uygula
    blur_image = cv2.GaussianBlur(gray_image, (3, 3), 1)

    # Aydınlatma farklarını tolere etmek için Adaptive Thresholding uygula
    thresh_image = cv2.adaptiveThreshold(
        blur_image, 
        255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 
        25, 
        16
    )

    kernel = np.ones((3, 3), np.uint8)
    processed_image = cv2.dilate(thresh_image, kernel, iterations=1)

    return processed_image