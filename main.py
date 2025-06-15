from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout # Using BoxLayout for content arrangement

from crt_widget import CRTEffectWidget

class CrtDemoApp(App):
    """
    A simple Kivy application to demonstrate the CRTEffectWidget.
    """
    def build(self):
        """
        Builds the Kivy application interface.

        Returns:
            CRTEffectWidget: The root widget of the application.
        """
        # 1. Create an instance of CRTEffectWidget. This will be our root widget.
        crt_effect_widget = CRTEffectWidget()

        # 2. Create a layout to hold the content that will be affected by the shader.
        # Using BoxLayout for structured content.
        content_layout = BoxLayout(
            orientation='vertical',
            spacing=20,  # Increased spacing
            padding=50,  # Increased padding
            size_hint=(0.7, 0.6), # Adjusted size_hint for a more centered look
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        # 3. Add a Label and a Button as children to this content layout.
        main_label = Label(
            text="CRT Effect Showcase",
            font_size='32sp', # Larger font
            size_hint_y=None,
            height=60, # Adjusted height
            bold=True
        )
        info_label = Label(
            text="The content you see here is rendered through the CRTEffectWidget.\n"
                 "It simulates display characteristics of an old CRT monitor,\n"
                 "including barrel distortion, scanlines, and vignetting.",
            font_size='18sp', # Slightly larger font
            halign='center',
            valign='middle',
            line_height=1.2 # Improved line spacing
        )
        test_button = Button(
            text="Interact with CRT!",
            size_hint_y=None,
            height=55, # Adjusted height
            font_size='20sp' # Larger font for button
        )

        def on_button_click(instance):
            if "Clicked" in instance.text:
                instance.text = "Interact with CRT!"
            else:
                instance.text = "Clicked! Effect still cool?"
        test_button.bind(on_press=on_button_click)

        separator_label = Label(
            text="~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~", # Decorative separator
            font_size='12sp',
            size_hint_y=None,
            height=30
        )

        content_layout.add_widget(main_label)
        content_layout.add_widget(info_label)
        content_layout.add_widget(test_button)
        content_layout.add_widget(separator_label)


        # 4. Add the content layout as a child to the CRTEffectWidget instance.
        crt_effect_widget.add_widget(content_layout)

        # 5. Return the CRTEffectWidget instance.
        return crt_effect_widget

if __name__ == '__main__':
    # It's good practice to set Window size here if a specific demo size is desired
    from kivy.core.window import Window
    Window.size = (1024, 768) # A common desktop resolution for demos
    CrtDemoApp().run()
