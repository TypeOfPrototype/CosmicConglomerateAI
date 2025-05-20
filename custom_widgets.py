# custom_widgets.py

from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.graphics import PushMatrix, PopMatrix, Scale, Translate

class ImageButton(ButtonBehavior, Image):
    text = StringProperty('')
    angle = NumericProperty(0)
    scale_x = NumericProperty(1)
    scale_y = NumericProperty(1)
    anim = ObjectProperty(None)  # Added property to hold animation references

    def __init__(self, **kwargs):
        self.coords = kwargs.pop('coords', (0, 0))
        super(ImageButton, self).__init__(**kwargs)
        self.bind(
            pos=self.update_transform,
            size=self.update_transform,
            angle=self.update_transform,
            scale_x=self.update_transform,
            scale_y=self.update_transform
        )

    def update_transform(self, *args):
        """
        Update the transformation of the button based on angle and scale properties.
        This method ensures that any transformations like scaling or rotating are applied correctly.
        """
        self.canvas.before.clear()
        with self.canvas.before:
            PushMatrix()
            Translate(self.center_x, self.center_y)
            Scale(x=self.scale_x, y=self.scale_y, origin=(0, 0))
            Translate(-self.center_x, -self.center_y)
        self.canvas.after.clear()
        with self.canvas.after:
            PopMatrix()
