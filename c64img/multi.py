"""
Fullscreen multicolor image abstraction.

Assumptions:
    - Input image 160x200 or 320x200 pixels. In case od 320 px width images,
      it will be resized to 160x200 internally.
    - Maximum 3 colors per char may be used, with one constant color
      (background) available across all of the chars
"""
from c64img import base


class MultiChar(base.Char):
    """Char implementation for multicolor mode."""

    def __init__(self, log, pixels_pairs, prev=None, fix_clash=False):
        """
        Init. prev is the Char object which represents the same character
        in previous picture
        """
        super(MultiChar, self).__init__(log, prev, fix_clash)
        self.background = [x
                           for x, y in pixels_pairs.items()
                           if y == (0, 0)][0]
        self.max_colors = 4
        self.global_pixel_pairs = pixels_pairs  # 1: (0, 1), 2: (1, 1)...
        self.pixel_state = {(0, 1): False,
                            (1, 0): False,
                            (1, 1): False}

    def _analyze_color_map(self):
        """
        Check for the optimal color placement in char. This method may be run
        only on not clashed chars. Background color should be always
        available.
        """
        self.colors[self.background] = (0, 0)
        super(MultiChar, self)._analyze_color_map()

    def _compare_colors(self, colors):
        """Overwritten compare colors routine"""

        for color in colors:
            pair = self.global_pixel_pairs.get(color)
            if pair is not None:
                self.pixel_state[pair] = True
                self.colors[color] = pair

        for color in colors:
            if color == self.background:
                continue
            if color in self.global_pixel_pairs:
                continue

            if not self.pixel_state[(1, 1)]:
                self.pixel_state[(1, 1)] = True
                self.colors[color] = (1, 1)
                continue

            if not self.pixel_state[(1, 0)]:
                if self.prev and self.prev.colors.get(color, None) is not None:
                    # XXX: how about case, where we have previous data vs
                    # global colors prediction. Have to checkit.
                    pass
                self.log.debug("Anomaly reserving state 1,0, %s", self.prev)
                self.pixel_state[(1, 0)] = True
                self.colors[color] = (1, 0)
                continue

            if not self.pixel_state[(0, 1)]:
                self.log.debug("Anomaly reserving state 0,1")
                self.pixel_state[(0, 1)] = True
                self.colors[color] = (0, 1)
                continue

        for color in colors:
            if color in self.colors:
                continue

            # XXX: same as above
            if self.prev and self.prev.colors.get(color, None) is not None:
                self.colors[color] = self.prev.colors[color]
                self.pixel_state[self.prev.colors[color]] = True

    def get_binary_data(self):
        """
        Return binary data for the char
        """
        result = {"bitmap": [], "screen-ram": 0, "color-ram": 0}

        for row in zip(*[iter(sorted(self.pixels))] * 4):
            char_line = 0
            for idx, pixel in enumerate(row):
                bits = self.colors.get(self.pixels[pixel], (0, 0))
                char_line += bits[0] * 2 ** (7 - idx * 2)
                char_line += bits[1] * 2 ** (6 - idx * 2)
            result["bitmap"].append(char_line)

        colors = dict([(y, x) for x, y in self.colors.items()])
        col1 = colors.get((0, 1), colors.get((0, 0))) * 16
        col2 = colors.get((1, 0), colors.get((0, 0)))

        result["color-ram"] = col1 + col2
        result["screen-ram"] = colors.get((1, 1), colors.get((0, 0)))

        return result


class MultiConverter(base.FullScreenImage):
    """
    Convert bitmap graphic in png/gif/probably other formats supported by
    PIL prepared as multicolor image into executable C64 prg file suitable
    to transfer to real thing or run in emulator.
    """
    WIDTH = 160
    HEIGHT = 200
    LOGGER_NAME = "MultiConverter"

    def __init__(self, fname, errors_action="none"):
        """
        Initialization
        """
        super(MultiConverter, self).__init__(fname, errors_action)
        self._scaled = False
        self._save_map = {"prg": self._save_prg,
                          "raw": self._save_raw,
                          "multi": self._save_koala,  # sane default
                          "koala": self._save_koala}

    def _load(self):
        """
        Load source image and store it under _src_image attribute.
        Shrink it if needed to 160x200 pixels.
        """
        if super(MultiConverter, self)._load():
            if self._src_image.size == (320, 200):
                self._src_image = self._src_image.resize((160, 200))
                self._scaled = True
            return True
        return False

    def _check_dimensions(self):
        """
        Check for image dimensions. If different from 320x200 or 160x200
        return False
        """
        result = super(MultiConverter, self)._check_dimensions()

        width, height = self._src_image.size
        if width == MultiConverter.WIDTH and height == MultiConverter.HEIGHT:
            return True

        if not result:
            self.log.error("Wrong picture dimensions: %dx%d", width, height)
        return result

    def _get_displayer(self):
        """
        Get displayer for multicolor picture (based on kickassembler example)
        """
        border = chr(self._get_border())
        background = chr(self._get_background())
        displayer = ["\x01\x08\x0b\x08\n\x00\x9e2064\x00\x00\x00\x00\x00\x00"
                     "\xa98\x8d\x18\xd0\xa9\xd8\x8d\x16\xd0\xa9;\x8d\x11\xd0"
                     "\xa9", border, "\x8d \xd0\xa9", background, "\x8d!\xd0"
                     "\xa2\x00\xbd\x00\x1c\x9d\x00\xd8\xbd\x00\x1d\x9d\x00"
                     "\xd9\xbd\x00\x1e\x9d\x00\xda\xbd\x00\x1f\x9d\x00\xdb"
                     "\xe8\xd0\xe5LF\x08"]

        return "".join(displayer)

    def _fill_memory(self):
        """
        Create bitmap, screen-ram, color-ram and error map as a picture if
        needed.
        """
        self.data["bitmap"] = []
        self.data["screen-ram"] = []
        self.data["color-ram"] = []
        self.data["background"] = self._get_background()
        self.data["chars"] = []
        used_color_pairs = {'can_be_chars': True}
        error_list = []
        pixel_state = {(0, 0): self.data['background']}

        for color in self.data['most_freq_colors']:
            if color == self.data['background']:
                continue
            if (0, 1) not in pixel_state:
                pixel_state[(0, 1)] = color
                continue
            if (1, 0) not in pixel_state:
                pixel_state[(1, 0)] = color
            break
        pixel_state = {y: x for x, y in pixel_state.items()}

        # get every char (4x8 pixels) starting from upper left corner
        for chry, chrx in [(chry, chrx)
                           for chry in range(0, self._src_image.size[1], 8)
                           for chrx in range(0, self._src_image.size[0], 4)]:

            box = self._src_image.crop((chrx, chry,
                                        chrx + 4, chry + 8)).convert("RGB")

            char = MultiChar(self.log,
                             pixel_state,
                             self.prev_chars.get((chry, chrx)),
                             self._errors_action == "fix")
            char.process(box, self._palette_map)
            self.chars[(chry, chrx)] = char

            char_data = char.get_binary_data()
            self.data['bitmap'].extend(char_data['bitmap'])
            self.data['screen-ram'].append(char_data['screen-ram'])
            self.data['color-ram'].append(char_data['color-ram'])

            self.prev_chars[(chry, chrx)] = char
            if char.clash:
                error_list.append((chrx, chry))
                self.log.error("Too many colors per block in char %d, %d near"
                               " x=%d, y=%d.",
                               chrx / 8 + 1,
                               chry / 8 + 1,
                               chrx + 4,
                               chry + 4)

            for color, pair in char.colors.items():
                if pair not in used_color_pairs:
                    used_color_pairs[pair] = color
                    continue

                if used_color_pairs[pair] != color and pair != (1, 1):
                    used_color_pairs['can_be_chars'] = False
                    break

        if error_list:
            self._error_image_action(error_list, self._scaled)
            return False

        if used_color_pairs['can_be_chars']:
            self.log.debug(used_color_pairs)
            del used_color_pairs['can_be_chars']
            used_color_pairs = {x: base.COLOR_NAMES[y]
                                for x, y in used_color_pairs.items()}
            self.log.info("Possible char conversion. Pixel pairs and "
                          "corresponding colors: %s", used_color_pairs)
        else:
            self.log.debug("Image cannot be converted to chars")

        self.log.info("Conversion successful.")
        return True

    def _save_prg(self, filename):
        """
        Save executable version of the picture
        """
        file_obj = open(filename, "wb")
        file_obj.write(self._get_displayer())
        file_obj.write(951 * chr(0))
        file_obj.write("".join([chr(col) for col in self.data["color-ram"]]))
        file_obj.write(3096 * chr(0))
        file_obj.write("".join([chr(col) for col in self.data["screen-ram"]]))
        file_obj.write(24 * chr(0))
        file_obj.write("".join([chr(byte) for byte in self.data["bitmap"]]))
        file_obj.close()
        self.log.info("Saved executable under `%s' file", filename)
        return True

    def _save_koala(self, filename):
        """
        Save as Koala format
        """
        file_obj = open(filename, "wb")
        file_obj.write("%c%c" % (0x00, 0x60))

        for char in self.data['bitmap']:
            file_obj.write("%c" % char)

        for char in self.data["color-ram"]:
            file_obj.write("%c" % char)

        for char in self.data["screen-ram"]:
            file_obj.write("%c" % char)

        file_obj.write(chr(self.data["background"]))

        file_obj.close()
        self.log.info("Saved in Koala format under `%s' file", filename)
        return True

    def _save_raw(self, filename):
        """
        Save as raw data
        """

        with open(filename + "_bitmap.raw", "wb") as file_obj:
            for char in self.data['bitmap']:
                file_obj.write("%c" % char)

        with open(filename + "_screen.raw", "wb") as file_obj:
            for char in self.data["screen-ram"]:
                file_obj.write("%c" % char)

        with open(filename + "_color-ram.raw", "wb") as file_obj:
            for char in self.data["color-ram"]:
                file_obj.write("%c" % char)

        with open(filename + "_bg.raw", "wb") as file_obj:
            file_obj.write(chr(self.data["background"]))

        self.log.info("Saved in raw format under `%s_*' files", filename)
        return True
