"""Displays to present stuff."""

from matplotlib import cm
try:
    from rgbmatrix import graphics
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
except ImportError:
    print('No RGB Matrix library found. Cannot use that display.')
    RGBMatrix = None

from infopanel import colors

class Display(object):
    """
    A display screen.

    This is a common interface to whatever kind of display you have.
    """
    def outlined_text(self, font, x, y, red, green, blue, outline_r, outline_g, outline_b, text):
        """Render text in a font to a place on the screen in a certain color."""
        raise NotImplementedError

    def text(self, font, x, y, red, green, blue, text):
        """Render text in a font to a place on the screen in a certain color."""
        raise NotImplementedError

    @property
    def width(self):
        """Width of the display in pixels."""
        raise NotImplementedError

    @property
    def height(self):
        """Height of the display in pixels."""
        raise NotImplementedError

    @property
    def brightness(self):
        """Brightness of display from 0 to 100."""
        raise NotImplementedError

    @brightness.setter
    def brightness(self, value):
        raise NotImplementedError

    def set_pixel(self, x, y, r, g, b):
        """Set a pixel to a color."""
        raise NotImplementedError

    def set_image(self, image, x=0, y=0):
        """Apply an image to the screen."""
        raise NotImplementedError

    def rainbow_text(self, font, x, y, text, box=True):
        """Make rainbow text."""
        x_orig = x
        for i, char in enumerate(text):
            r, g, b = colors.interpolate_color(float(i) / len(text), cmap=cm.gist_rainbow)  # pylint: disable=no-member
            x += self.text(font, x, y, r, g, b, char)
        if box:
            self.draw_box(x_orig - 2, y - font.height + 2, x, y + 2)

    def draw_box(self, xmin, ymin, xmax, ymax, r=0, g=200, b=0):
        """Don't use PIL because it blanks.  NOTE: Use graphics.DrawLine"""
        for x in range(xmin, xmax):
            self.set_pixel(x, ymin, r, g, b)
            self.set_pixel(x, ymax, r, g, b)

        for y in range(ymin, ymax + 1):
            self.set_pixel(xmin, y, r, g, b)
            self.set_pixel(xmax, y, r, g, b)

    def draw_rect(self, xpos, ypos, width, height, color):
        raise NotImplementedError

class RGBMatrixDisplay(Display):
    """An RGB LED Matrix running off of the rgbmatrix library."""
    def __init__(self, matrix):
        Display.__init__(self)
        self._matrix = matrix
        self.canvas = matrix.CreateFrameCanvas()
        self.black = graphics.Color(0, 0, 0)

    @property
    def width(self):
        """Width of the display in pixels."""
        return self._matrix.width

    @property
    def height(self):
        """Height of the display in pixels."""
        return self._matrix.height

    @property
    def brightness(self):
        """Brightness of display from 0 to 100."""
        return self._matrix.brightness

    @brightness.setter
    def brightness(self, value):
        self._matrix.brightness = value
        self.canvas.brightness = value

    def draw_rect(self, xpos, ypos, width, height, color):
        xmax = min(xpos + width, 32)
        ymax = min(ypos + height, 32)
        xmin = max(xpos, 0)
        for y in range(ypos, ymax):
            graphics.DrawLine(self.canvas, xmin, y, xmax, y, color)

    def outlined_text(self, font, x, y, red, green, blue, outline_r, outline_g, outline_b, text):
        outline_color = graphics.Color(0, 200, 0)
        box_width = (len(text) * 5)+2
        self.draw_rect(x - 1, y - font.height + 1, box_width, y + 2, outline_color)

        color = graphics.Color(red, green, blue)  # may require caching
        return graphics.DrawText(self.canvas, font, x, y, color, text)

    def text(self, font, x, y, red, green, blue, text):
        """Render text in a font to a place on the screen in a certain color."""
        color = graphics.Color(red, green, blue)  # may require caching
        return graphics.DrawText(self.canvas, font, x, y, color, text)

    def set_pixel(self, x, y, red, green, blue):
        """Set a pixel to a color."""
        self.canvas.SetPixel(x, y, red, green, blue)

    def set_image(self, image, x=0, y=0):
        """Apply an image to the screen."""
        self.canvas.SetImage(image, x, y)

    def clear(self):
        """Clear the canvas."""
        self.canvas.Clear()

    def buffer(self):
        """Swap the off-display canvas/buffer with the on-display one."""
        self.canvas = self._matrix.SwapOnVSync(self.canvas)


def rgbmatrix_options_factory(config):
    """Build RGBMatrix options object."""
    options = RGBMatrixOptions()
    if config['led-gpio-mapping'] != None:
        options.hardware_mapping = config['led-gpio-mapping']
    options.rows = config['led-rows']
    options.chain_length = config['led-chain']
    options.parallel = config['led-parallel']
    options.pwm_bits = config['led-pwm-bits']
    options.brightness = config['led-brightness']
    options.pwm_lsb_nanoseconds = config['led-pwm-lsb-nanoseconds']
    if config['led-show-refresh']:
        options.show_refresh_rate = 1
    if config['led-slowdown-gpio'] != None:
        options.gpio_slowdown = config['led-slowdown-gpio']
    if config['led-no-hardware-pulse']:
        options.disable_hardware_pulsing = True
    return options

def display_factory(config):
    """Build a display based on config settings."""

    if 'RGBMatrix' in config:
        if RGBMatrix is None:
            return Display()
        options = rgbmatrix_options_factory(config['RGBMatrix'])
        matrix = RGBMatrix(options=options)
        display = RGBMatrixDisplay(matrix)
    else:
        raise ValueError('Unknown Display options. Check config file.')
    return display
