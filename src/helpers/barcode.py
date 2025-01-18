import os
from pyzbar.pyzbar import decode, ZBarSymbol
from PIL import Image

def read_barcodes(image_path):
    """
    Returns all read barcodes found in the image given by the path
    """
    #img = cv2.imdecode(img_data, cv.IMREAD_UNCHAGED) # Read raw data
    #img = cv2.imread(image_path)
    #bd = cv2.barcode.BarcodeDetector()

    #retval, points, straight_code = bd.detectAndDecode(img)

    objs = decode(
        Image.open(image_path),
        symbols=[
            ZBarSymbol.EAN2, ZBarSymbol.EAN5, ZBarSymbol.EAN8, ZBarSymbol.EAN13
        ]
    )

    os.remove(image_path)

    eans = list(map(lambda e: int(e.data), objs))

    return eans