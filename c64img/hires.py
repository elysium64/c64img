"""
Fullscreen high resolution image abstraction.

Assumptions:
    - Input image 320x200 pixels.
    - Maximum 2 colors per char may be used.
"""
from c64img import base


class HiresChar(base.Char):
    """
    Hires char implementation
    """

    def get_binary_data(self):
        """
        Return binary data for the char
        """
        result = {"bitmap": [], "screen-ram": 0}

        pixel_keys = sorted(self.pixels.keys())

        for key_row in [pixel_keys[index:index+8]
                        for index in range(0, len(pixel_keys), 8)]:
            char_line = 0
            for key in key_row:
                bit_ = self.colors.get(self.pixels[key], 0)
                char_line += bit_ * 2 ** (7 - key[1])
            result['bitmap'].append(char_line)

        colors = dict([(y, x) for x, y in self.colors.items()])
        if 0 in colors:
            result['screen-ram'] = colors[0]

        if 1 in colors:
            result['screen-ram'] += colors[1] * 16
        return result


class HiresConverter(base.FullScreenImage):
    """
    Convert bitmap graphic in png/gif/probably other formats supported by
    PIL into executable C64 prg file suitable to transfer to real thing or
    run in emulator.
    """
    LOGGER_NAME = "HiresConverter"

    def __init__(self, fname, errors_action="none"):
        """
        Initialization
        """
        super(HiresConverter, self).__init__(fname, errors_action)
        self._save_map = {"prg": self._save_prg,
                          "raw": self._save_raw,
                          "hires": self._save_ash,  # make sane default
                          "art-studio-hires": self._save_ash}

    def _get_displayer(self):
        """
        Get displayer for hires picture
        """
        return bytearray([0x01, 0x08, 0x0b, 0x08, 0x0a, 0x00, 0x9e, 0x32,
                          0x30, 0x36, 0x34, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x78, 0xa9, self._get_border(), 0x8d, 0x20,
                          0xd0, 0xa9, 0x00, 0x8d, 0x21, 0xd0, 0xa9, 0xbb,
                          0x8d, 0x11, 0xd0, 0xa9, 0x3c, 0x8d, 0x18, 0xd0,
                          0x4c, 0x25, 0x08])

    def _fill_memory(self):
        """
        Create bitmap/screen and error map as a picture if needed.
        """
        self.data["bitmap"] = []
        self.data["screen-ram"] = []
        error_list = []

        for chry, chrx in [(chry, chrx)
                           for chry in range(0, self._src_image.size[1], 8)
                           for chrx in range(0, self._src_image.size[0], 8)]:

            box = self._src_image.crop((chrx, chry,
                                        chrx + 8, chry + 8)).convert("RGB")

            char = HiresChar(self.log,
                             self.prev_chars.get((chry, chrx)),
                             self._errors_action == "fix")
            char.process(box, self._palette_map)
            self.chars[(chry, chrx)] = char

            char_data = char.get_binary_data()
            self.data['bitmap'].extend(char_data['bitmap'])
            self.data['screen-ram'].append(char_data['screen-ram'])

            if char.clash:
                error_list.append((chrx, chry))
                self.log.error("Too many colors per block in char %d, %d near"
                               " x=%d, y=%d.",
                               chrx / 8 + 1,
                               chry / 8 + 1,
                               chrx + 4,
                               chry + 4)

        if error_list:
            self._error_image_action(error_list)
            return False

        self.log.info("Conversion successful.")
        return True

    def _save_prg(self, filename):
        """
        Save executable version of the picture
        """
        file_obj = open(filename, "wb")
        file_obj.write(self._get_displayer())
        file_obj.write(984 * b'\x00')
        file_obj.write(bytearray(self.data["screen-ram"]))
        file_obj.write(4120 * b'\x00')
        file_obj.write(bytearray(self.data["bitmap"]))
        file_obj.close()
        self.log.info("Saved executable under `%s' file", filename)
        return True

    def _save_ash(self, filename):
        """
        Save as Art Studio hires
        """
        file_obj = open(filename, "wb")
        file_obj.write(bytearray([0x00, 0x20]))
        file_obj.write(bytearray(self.data['bitmap']))
        file_obj.write(bytearray(self.data["screen-ram"]))
        file_obj.write(bytearray([self._get_border()]))
        file_obj.write(6 * b'\x00')
        file_obj.close()
        self.log.info("Saved in Art Studio Hires format under `%s' file",
                      filename)
        return True

    def _save_raw(self, filename):
        """
        Save raw data
        """
        with open(filename + "_screen.raw", "wb") as file_obj:
            file_obj.write(bytearray(self.data["screen-ram"]))

        with open(filename + "_bitmap.raw", "wb") as file_obj:
            file_obj.write(bytearray(self.data["bitmap"]))

        self.log.info("Saved raw data under `%s_*' files", filename)
        return True

    def _check_dimensions(self):
        """
        Check for image dimensions. Same as in superclass, needed for feedback
        only.
        """
        result = super(HiresConverter, self)._check_dimensions()
        width, height = self._src_image.size

        if not result:
            self.log.error("Wrong picture dimensions: %dx%d", width, height)

        return result
