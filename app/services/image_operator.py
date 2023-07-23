import pytesseract
import cv2
import os
import io
import numpy as np
from PIL import Image


class ImageOperator:

    def parse_image_to_string(self, image: str, preprocess: str = 'thresh') -> str:
        # загрузить образ и преобразовать его в оттенки серого
        image = cv2.imread(image)
        gray: np.ndarray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # проверьте, следует ли применять пороговое значение для предварительной обработки изображения
        if preprocess == "thresh":
            gray = cv2.threshold(gray, 0, 255,
                                 cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        # если нужно медианное размытие, чтобы удалить шум
        elif preprocess == "blur":
            gray = cv2.medianBlur(gray, 3)

        success, encoded_image = cv2.imencode('.jpg', gray)
        buffer = io.BytesIO(encoded_image.tobytes())

        # загрузка изображения в виде объекта image Pillow, применение OCR, а затем удаление временного файла
        text = pytesseract.image_to_string(Image.open(buffer), lang='rus')

        return text

    def convert_string_to_data(self, mess: str):
        lines: list[str] = [line for line in mess.split('\n') if line]
        return lines


image_operator = ImageOperator()

path = '/Users/zhbankov.da/telegram_bot_notionAPI/app/test.jpeg'

text = image_operator.parse_image_to_string(path)

print(image_operator.convert_string_to_data(text))
