from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading


def create_default_images():
    size = 800
    template = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([0, 0, size, size], fill=255)
    
    draw = ImageDraw.Draw(template)
    
    for i in range(10):
        gray = 20 + i * 3
        radius = 400 - i * 5
        draw.ellipse([400-radius, 400-radius, 400+radius, 400+radius], 
                     fill=(gray, gray, gray, 255))
    
    draw.ellipse([290, 290, 510, 510], fill=(30, 30, 30, 255))
    
    for i in range(50):
        radius = 380 - i * 6
        color = 15 + (i % 3) * 5
        draw.ellipse([400-radius, 400-radius, 400+radius, 400+radius], 
                     outline=(color, color, color, 100), width=1)
    
    template.putalpha(mask)
    template.save('vinyl_template.png', 'PNG')
    
    capa = Image.new('RGBA', (600, 600), (0, 0, 0, 0))
    capa.save('cover.png', 'PNG')
    
    rotulo = Image.new('RGB', (400, 400), (200, 200, 200))
    draw = ImageDraw.Draw(rotulo)
    
    draw.ellipse([0, 0, 400, 400], fill=(220, 180, 80))
    draw.ellipse([20, 20, 380, 380], fill=(240, 200, 100))
    
    try:
        font_label = ImageFont.truetype("arial.ttf", 50)
        font_small_label = ImageFont.truetype("arial.ttf", 30)
    except:
        font_label = ImageFont.load_default()
        font_small_label = ImageFont.load_default()
    
    draw.text((200, 160), "SIDE A", fill=(0, 0, 0), anchor="mm", font=font_label)
    draw.text((200, 240), "Label Records", fill=(50, 50, 50), anchor="mm", font=font_small_label)
    
    rotulo.save('label.png', 'PNG')
    
    print("✓ Default images created successfully!")


def check_and_create_defaults():
    files = ['vinyl_template.png', 'cover.png', 'label.png']
    missing = [f for f in files if not os.path.exists(f)]
    
    if missing:
        print(f"Creating default files: {', '.join(missing)}")
        create_default_images()
    
    return all(os.path.exists(f) for f in files)


def load_and_resize_image(image_path, target_size=None, maintain_aspect=True):
    img = Image.open(image_path).convert('RGBA')
    
    if target_size and maintain_aspect:
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
    elif target_size:
        img = img.resize(target_size, Image.Resampling.LANCZOS)
    
    return img


def create_circular_mask(size, feather=0, hole_size=0):
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([0, 0, size, size], fill=255)
    
    if hole_size > 0:
        center = size // 2
        draw.ellipse([center - hole_size, center - hole_size, 
                     center + hole_size, center + hole_size], fill=0)
    
    if feather > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(feather))
    
    return mask


def add_shadow(image, offset=(10, 10), blur=15, opacity=0.5):
    shadow_size = (
        image.width + abs(offset[0]) + blur * 2,
        image.height + abs(offset[1]) + blur * 2
    )
    shadow_canvas = Image.new('RGBA', shadow_size, (0, 0, 0, 0))
    
    shadow = Image.new('RGBA', image.size, (0, 0, 0, int(255 * opacity)))
    shadow_pos = (
        blur + max(0, offset[0]),
        blur + max(0, offset[1])
    )
    shadow_canvas.paste(shadow, shadow_pos, image)
    shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(blur))
    
    img_pos = (blur - min(0, offset[0]), blur - min(0, offset[1]))
    shadow_canvas.paste(image, img_pos, image)
    
    return shadow_canvas


def rotate_image_with_transparency(image, angle):
    if angle == 0:
        return image.copy()
    
    padding = int(max(image.size) * 0.8)
    padded_size = (image.width + padding * 2, image.height + padding * 2)
    padded = Image.new('RGBA', padded_size, (0, 0, 0, 0))
    padded.paste(image, (padding, padding), image)
    
    rotated = padded.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False)
    
    crop_box = (padding, padding, padding + image.width, padding + image.height)
    result = rotated.crop(crop_box)
    
    return result


def is_image_transparent(img):
    if img.mode != 'RGBA':
        return False
    extrema = img.getextrema()
    if len(extrema) < 4:
        return False
    return extrema[3][1] == 0


def create_vinyl_mockup(template_path, cover_path, label_path, output_path='mockup.png',
                        cover_scale=0.7, label_scale=0.28, rotation_angle=0, add_shadow_effect=True,
                        hole_size_percent=8):
    template = load_and_resize_image(template_path)
    template_width, template_height = template.size
    
    canvas = Image.new('RGBA', (template_width, template_height), (0, 0, 0, 0))
    
    cover = load_and_resize_image(cover_path)
    if not is_image_transparent(cover):
        cover_size = int(min(template_width, template_height) * cover_scale)
        cover = load_and_resize_image(cover_path, (cover_size, cover_size), maintain_aspect=False)
        
        if add_shadow_effect:
            cover = add_shadow(cover, offset=(8, 8), blur=12, opacity=0.4)
        
        cover_x = int(template_width * 0.05)
        cover_y = int(template_height * 0.05)
        canvas.paste(cover, (cover_x, cover_y), cover)
    
    vinyl_template = template.copy()
    if rotation_angle != 0:
        expanded_size = int(max(vinyl_template.size) * 2.5)
        expanded = Image.new('RGBA', (expanded_size, expanded_size), (0, 0, 0, 0))
        offset = (expanded_size - vinyl_template.width) // 2
        expanded.paste(vinyl_template, (offset, offset), vinyl_template)
        
        rotated = expanded.rotate(rotation_angle, resample=Image.Resampling.BICUBIC, expand=False)
        
        vinyl_template = rotated.crop((offset, offset, offset + template.width, offset + template.height))
        
        vinyl_mask = Image.new('L', vinyl_template.size, 0)
        mask_draw = ImageDraw.Draw(vinyl_mask)
        center = vinyl_template.width // 2
        mask_draw.ellipse([5, 5, vinyl_template.width - 5, vinyl_template.height - 5], fill=255)
        vinyl_template.putalpha(vinyl_mask)
    
    canvas.paste(vinyl_template, (0, 0), vinyl_template)
    
    label_diameter = int(min(template_width, template_height) * label_scale)
    label = load_and_resize_image(label_path, (label_diameter, label_diameter), maintain_aspect=False)
    
    if rotation_angle != 0:
        label = rotate_image_with_transparency(label, rotation_angle)
    
    circular_mask = create_circular_mask(label_diameter, feather=2, hole_size=0)
    label.putalpha(circular_mask)
    
    label_x = (template_width - label.width) // 2
    label_y = (template_height - label.height) // 2
    canvas.paste(label, (label_x, label_y), label)
    
    hole_radius = int(label_diameter * (hole_size_percent / 100.0))
    center = template_width // 2
    
    final_mask = canvas.split()[3]
    hole_draw = ImageDraw.Draw(final_mask)
    hole_draw.ellipse([center - hole_radius, center - hole_radius,
                      center + hole_radius, center + hole_radius], fill=0)
    canvas.putalpha(final_mask)
    
    canvas.save(output_path, 'PNG')
    print(f"Mockup saved at: {output_path}")
    
    return canvas


def create_vinyl_animation(template_path, cover_path, label_path, output_gif='mockup.gif',
                          num_frames=60, duration=50, loop=0, label_scale=0.28, hole_size_percent=8):
    frames = []
    
    print(f"Generating {num_frames} frames for animation...")
    
    frames_folder = 'frames_png'
    if not os.path.exists(frames_folder):
        os.makedirs(frames_folder)
    
    for i in range(num_frames):
        angle = -(360 / num_frames) * i
        frame_output = os.path.join(frames_folder, f'frame_{i:03d}.png')
        
        frame = create_vinyl_mockup(template_path, cover_path, label_path,
                                   output_path=frame_output, rotation_angle=angle,
                                   add_shadow_effect=True, label_scale=label_scale,
                                   hole_size_percent=hole_size_percent)
        
        alpha = frame.split()[3]
        frame_rgb = frame.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
        
        mask_image = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
        frame_rgb.paste(255, mask_image)
        frame_rgb.info['transparency'] = 255
        
        frames.append(frame_rgb)
        
        print(f"Frame {i+1}/{num_frames} complete (saved as PNG)")
    
    frames[0].save(output_gif, save_all=True, append_images=frames[1:],
                   duration=duration, loop=loop, optimize=False, disposal=2, transparency=255)
    
    print(f"GIF saved at: {output_gif}")
    print(f"PNG frames saved at: {frames_folder}/")
    return frames_folder


class VinylMockupGUI:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Vinyl Mockup Generator")
        self.root.geometry("650x600")
        self.root.resizable(False, False)
        
        self.template_path = tk.StringVar(value='vinyl_template.png')
        self.cover_path = tk.StringVar(value='cover.png')
        self.label_path = tk.StringVar(value='label.png')
        self.num_frames = tk.IntVar(value=60)
        self.gif_speed = tk.IntVar(value=50)
        self.label_size = tk.DoubleVar(value=28)
        self.hole_size = tk.DoubleVar(value=8)
        self.create_gif_var = tk.BooleanVar(value=False)
        
        self.setup_ui()
        
    def setup_ui(self):
        bg_color = '#1e1e1e'
        fg_color = '#ffffff'
        entry_bg = '#2d2d2d'
        button_bg = '#0078d4'
        
        self.root.configure(bg=bg_color)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color, font=('Segoe UI', 10))
        style.configure('TButton', background=button_bg, foreground=fg_color, 
                       borderwidth=0, focuscolor='none', font=('Segoe UI', 10))
        style.map('TButton', background=[('active', '#1e88e5')])
        style.configure('TCheckbutton', background=bg_color, foreground=fg_color, font=('Segoe UI', 10))
        style.map('TCheckbutton', background=[('active', bg_color)], foreground=[('active', fg_color)])
        style.configure('TLabelframe', background=bg_color, foreground=fg_color, 
                       borderwidth=1, relief='solid')
        style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color, 
                       font=('Segoe UI', 10, 'bold'))
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        title = tk.Label(main_frame, text="🎵 Vinyl Mockup Generator", 
                        font=('Segoe UI', 18, 'bold'), bg=bg_color, fg='#4fc3f7')
        title.grid(row=0, column=0, columnspan=3, pady=(0, 25))
        
        row = 1
        tk.Label(main_frame, text="Vinyl Template:", bg=bg_color, fg=fg_color, 
                font=('Segoe UI', 10)).grid(row=row, column=0, sticky=tk.W, pady=8)
        entry1 = tk.Entry(main_frame, textvariable=self.template_path, width=35, 
                         bg=entry_bg, fg=fg_color, insertbackground=fg_color, 
                         relief='flat', font=('Segoe UI', 9))
        entry1.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5, ipady=5)
        ttk.Button(main_frame, text="Browse", 
                  command=lambda: self.browse_file(self.template_path)).grid(row=row, column=2)
        
        row += 1
        tk.Label(main_frame, text="Album Cover:", bg=bg_color, fg=fg_color, 
                font=('Segoe UI', 10)).grid(row=row, column=0, sticky=tk.W, pady=8)
        entry2 = tk.Entry(main_frame, textvariable=self.cover_path, width=35, 
                         bg=entry_bg, fg=fg_color, insertbackground=fg_color, 
                         relief='flat', font=('Segoe UI', 9))
        entry2.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5, ipady=5)
        ttk.Button(main_frame, text="Browse", 
                  command=lambda: self.browse_file(self.cover_path)).grid(row=row, column=2)
        
        row += 1
        tk.Label(main_frame, text="Vinyl Label:", bg=bg_color, fg=fg_color, 
                font=('Segoe UI', 10)).grid(row=row, column=0, sticky=tk.W, pady=8)
        entry3 = tk.Entry(main_frame, textvariable=self.label_path, width=35, 
                         bg=entry_bg, fg=fg_color, insertbackground=fg_color, 
                         relief='flat', font=('Segoe UI', 9))
        entry3.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5, ipady=5)
        ttk.Button(main_frame, text="Browse", 
                  command=lambda: self.browse_file(self.label_path)).grid(row=row, column=2)
        
        row += 1
        tk.Label(main_frame, text="Label Size (%):", bg=bg_color, fg=fg_color, 
                font=('Segoe UI', 10)).grid(row=row, column=0, sticky=tk.W, pady=8)
        label_scale = tk.Scale(main_frame, from_=15, to=50, orient=tk.HORIZONTAL,
                              variable=self.label_size, bg=entry_bg, fg=fg_color,
                              highlightthickness=0, troughcolor='#3d3d3d', 
                              activebackground=button_bg, length=200)
        label_scale.grid(row=row, column=1, sticky=tk.W, padx=5)
        
        row += 1
        tk.Label(main_frame, text="Hole Size (%):", bg=bg_color, fg=fg_color, 
                font=('Segoe UI', 10)).grid(row=row, column=0, sticky=tk.W, pady=8)
        hole_scale = tk.Scale(main_frame, from_=3, to=20, orient=tk.HORIZONTAL,
                             variable=self.hole_size, bg=entry_bg, fg=fg_color,
                             highlightthickness=0, troughcolor='#3d3d3d', 
                             activebackground=button_bg, length=200, resolution=0.5)
        hole_scale.grid(row=row, column=1, sticky=tk.W, padx=5)
        
        row += 1
        separator = tk.Frame(main_frame, height=2, bg='#3d3d3d')
        separator.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        
        row += 1
        animation_frame = ttk.LabelFrame(main_frame, text="  GIF Animation (Optional)  ", 
                                        padding="15")
        animation_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Checkbutton(animation_frame, text="Create GIF animation", 
                       variable=self.create_gif_var,
                       command=self.toggle_frames).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=8)
        
        self.frames_label = tk.Label(animation_frame, text="Frames:", bg=bg_color, 
                                     fg=fg_color, font=('Segoe UI', 10), state='disabled')
        self.frames_label.grid(row=1, column=0, sticky=tk.W, padx=(20, 5))
        
        self.frames_scale = tk.Scale(animation_frame, from_=10, to=120, orient=tk.HORIZONTAL,
                                     variable=self.num_frames, bg=entry_bg, fg=fg_color,
                                     highlightthickness=0, troughcolor='#3d3d3d',
                                     activebackground=button_bg, length=150, state='disabled')
        self.frames_scale.grid(row=1, column=1, sticky=tk.W)
        
        self.speed_label = tk.Label(animation_frame, text="Speed (ms):", bg=bg_color, 
                                    fg=fg_color, font=('Segoe UI', 10), state='disabled')
        self.speed_label.grid(row=2, column=0, sticky=tk.W, padx=(20, 5), pady=8)
        
        self.speed_scale = tk.Scale(animation_frame, from_=10, to=200, orient=tk.HORIZONTAL,
                                    variable=self.gif_speed, bg=entry_bg, fg=fg_color,
                                    highlightthickness=0, troughcolor='#3d3d3d',
                                    activebackground=button_bg, length=150, state='disabled')
        self.speed_scale.grid(row=2, column=1, sticky=tk.W)
        
        row += 1
        self.generate_btn = tk.Button(main_frame, text="🎨 Generate Mockup", 
                                     command=self.generate_mockup, bg=button_bg, fg=fg_color,
                                     font=('Segoe UI', 12, 'bold'), relief='flat', 
                                     cursor='hand2', pady=12)
        self.generate_btn.grid(row=row, column=0, columnspan=3, pady=20, sticky=(tk.W, tk.E))
        
        row += 1
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=500)
        self.progress.grid(row=row, column=0, columnspan=3, pady=5)
        
        row += 1
        self.status_label = tk.Label(main_frame, text="Ready to generate mockup", 
                                     font=('Segoe UI', 9), bg=bg_color, fg='#888888')
        self.status_label.grid(row=row, column=0, columnspan=3)
        
        row += 1
        default_btn = tk.Button(main_frame, text="Create Default Images", 
                               command=self.create_defaults_ui, bg='#2d2d2d', fg=fg_color,
                               font=('Segoe UI', 9), relief='flat', cursor='hand2', pady=8)
        default_btn.grid(row=row, column=0, columnspan=3, pady=(10, 0), sticky=(tk.W, tk.E))
        
    def browse_file(self, var):
        filename = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
        )
        if filename:
            var.set(filename)
    
    def toggle_frames(self):
        state = 'normal' if self.create_gif_var.get() else 'disabled'
        self.frames_label.config(state=state)
        self.frames_scale.config(state=state)
        self.speed_label.config(state=state)
        self.speed_scale.config(state=state)
    
    def create_defaults_ui(self):
        try:
            create_default_images()
            self.status_label.config(text="Default images created!", fg='#4caf50')
        except Exception as e:
            self.status_label.config(text=f"Error creating defaults: {str(e)}", fg='#f44336')
    
    def generate_mockup(self):
        files = [self.template_path.get(), self.cover_path.get(), self.label_path.get()]
        missing = [f for f in files if not os.path.exists(f)]
        
        if missing:
            self.status_label.config(text="Files not found! Click 'Create Default Images'", fg='#f44336')
            return
        
        self.generate_btn.config(state='disabled')
        self.progress.start(10)
        self.status_label.config(text="Generating mockup...", fg='#2196f3')
        
        thread = threading.Thread(target=self.generate_worker)
        thread.start()
    
    def generate_worker(self):
        try:
            label_scale = self.label_size.get() / 100.0
            hole_size = self.hole_size.get()
            
            create_vinyl_mockup(
                template_path=self.template_path.get(),
                cover_path=self.cover_path.get(),
                label_path=self.label_path.get(),
                output_path='mockup.png',
                cover_scale=0.7,
                label_scale=label_scale,
                rotation_angle=5,
                add_shadow_effect=True,
                hole_size_percent=hole_size
            )
            
            if self.create_gif_var.get():
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Generating GIF animation ({self.num_frames.get()} frames)...", 
                    fg='#2196f3'))
                
                frames_folder = create_vinyl_animation(
                    template_path=self.template_path.get(),
                    cover_path=self.cover_path.get(),
                    label_path=self.label_path.get(),
                    output_gif='mockup.gif',
                    num_frames=self.num_frames.get(),
                    duration=self.gif_speed.get(),
                    loop=0,
                    label_scale=label_scale,
                    hole_size_percent=hole_size
                )
                self.root.after(0, lambda: self.status_label.config(
                    text=f"✓ Mockup generated! Check mockup.png, mockup.gif & {frames_folder}/", 
                    fg='#4caf50'))
            else:
                self.root.after(0, lambda: self.status_label.config(
                    text="✓ Mockup generated successfully! Check mockup.png", 
                    fg='#4caf50'))
            
            self.root.after(0, lambda: self.generation_complete())
            
        except Exception as e:
            self.root.after(0, lambda: self.generation_error(str(e)))
    
    def generation_complete(self):
        self.progress.stop()
        self.generate_btn.config(state='normal')
    
    def generation_error(self, error):
        self.progress.stop()
        self.generate_btn.config(state='normal')
        self.status_label.config(text=f"Error generating mockup: {error}", fg='#f44336')


def main():
    check_and_create_defaults()
    
    root = tk.Tk()
    app = VinylMockupGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
