from PIL import Image

IMAGE_SIZE = 48


def crop_and_scale(path):
    path = str(path)
    symbol = Image.open(path)
    width, height = symbol.size
    length = max(width, height)
    background = Image.new("RGB", (length, length), "WHITE")
    x_offset = (length - width) // 2
    y_offset = (length - height) // 2
    background.paste(symbol, box=(x_offset, y_offset))
    background = background.resize(
        (IMAGE_SIZE, IMAGE_SIZE), resample=Image.BILINEAR)
    background.save(path)
