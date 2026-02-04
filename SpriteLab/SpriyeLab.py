import pygame
import pygame_gui
import json
import os
from datetime import datetime
from PIL import Image, ImageDraw
import io

class PixelArtEditor:
    def __init__(self):
        pygame.init()
        
        self.WIDTH = 1200
        self.HEIGHT = 800
        self.CANVAS_SIZE = 32
        self.PIXEL_SIZE = 20
        self.CANVAS_WIDTH = self.CANVAS_SIZE * self.PIXEL_SIZE
        
        self.BG_COLOR = pygame.Color(40, 44, 52)
        self.UI_BG_COLOR = pygame.Color(33, 37, 43)
        self.GRID_COLOR = pygame.Color(60, 64, 72)
        
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("SpriteLab - Pixel Art Editor")
        
        self.manager = pygame_gui.UIManager((self.WIDTH, self.HEIGHT))
        
        self.canvas_surface = pygame.Surface((self.CANVAS_WIDTH, self.CANVAS_WIDTH))
        self.canvas_surface.fill((255, 255, 255))
        self.canvas_rect = pygame.Rect(20, 20, self.CANVAS_WIDTH, self.CANVAS_WIDTH)
        
        self.current_color = pygame.Color(0, 0, 0)
        self.current_tool = "brush"
        self.is_drawing = False
        self.last_pos = None
        
        self.history = []
        self.save_state()
        
        self.palettes = {
            "Basic": [
                (0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 255, 0),
                (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255),
                (128, 0, 0), (0, 128, 0), (0, 0, 128), (128, 128, 0)
            ],
            "Pastel": [
                (255, 209, 220), (204, 255, 229), (204, 229, 255),
                (255, 255, 204), (229, 204, 255), (255, 229, 204),
                (220, 255, 209), (209, 220, 255), (255, 204, 229)
            ],
            "Game Boy": [
                (15, 56, 15), (48, 98, 48), (139, 172, 15),
                (155, 188, 15), (48, 98, 48)
            ],
            "NES": [
                (124, 124, 124), (0, 0, 252), (0, 0, 188), (68, 40, 188),
                (148, 0, 132), (168, 0, 32), (168, 16, 0), (136, 20, 0)
            ]
        }
        
        self.current_palette = "Basic"
        
        self.frames = [self.canvas_surface.copy()]
        self.current_frame = 0
        self.is_animating = False
        self.animation_speed = 5
        
        self.create_ui()
        
    def create_ui(self):
        tool_panel_rect = pygame.Rect(self.CANVAS_WIDTH + 40, 20, self.WIDTH - self.CANVAS_WIDTH - 60, 200)
        self.tool_panel = pygame_gui.elements.UIPanel(relative_rect=tool_panel_rect, manager=self.manager, object_id="tool_panel")
        
        self.brush_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10, 10, 100, 40), text="Brush", manager=self.manager, container=self.tool_panel)
        
        self.fill_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(120, 10, 100, 40), text="Fill", manager=self.manager, container=self.tool_panel)
        
        self.line_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(230, 10, 100, 40), text="Line", manager=self.manager, container=self.tool_panel)
        
        self.erase_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(340, 10, 100, 40), text="Eraser", manager=self.manager, container=self.tool_panel)
        
        self.color_label = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, 60, 200, 30), text="Color:", manager=self.manager, container=self.tool_panel)
        
        color_btn_rect = pygame.Rect(220, 60, 50, 30)
        self.color_picker = pygame_gui.elements.UIButton(relative_rect=color_btn_rect, text="", manager=self.manager, container=self.tool_panel, object_id='#color_picker')
        
        self.palette_label = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, 100, 200, 30), text="Palette:", manager=self.manager, container=self.tool_panel)
        
        self.palette_dropdown = pygame_gui.elements.UIDropDownMenu(options_list=list(self.palettes.keys()), starting_option=self.current_palette, relative_rect=pygame.Rect(120, 100, 150, 30), manager=self.manager, container=self.tool_panel)
        
        anim_panel_rect = pygame.Rect(self.CANVAS_WIDTH + 40, 230, self.WIDTH - self.CANVAS_WIDTH - 60, 200)
        self.anim_panel = pygame_gui.elements.UIPanel(relative_rect=anim_panel_rect, manager=self.manager, object_id="anim_panel")
        
        self.add_frame_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10, 10, 120, 40), text="+ Frame", manager=self.manager, container=self.anim_panel)
        
        self.remove_frame_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(140, 10, 120, 40), text="- Frame", manager=self.manager, container=self.anim_panel)
        
        self.play_anim_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(270, 10, 120, 40), text="▶ Play", manager=self.manager, container=self.anim_panel)
        
        self.frame_label = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, 60, 200, 30), text=f"Frame: {self.current_frame + 1}/{len(self.frames)}", manager=self.manager, container=self.anim_panel)
        
        self.speed_label = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, 100, 100, 30), text="Speed:", manager=self.manager, container=self.anim_panel)
        
        self.speed_slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(120, 100, 150, 30), start_value=self.animation_speed, value_range=(1, 30), manager=self.manager, container=self.anim_panel)
        
        export_panel_rect = pygame.Rect(self.CANVAS_WIDTH + 40, 440, self.WIDTH - self.CANVAS_WIDTH - 60, 200)
        self.export_panel = pygame_gui.elements.UIPanel(relative_rect=export_panel_rect, manager=self.manager, object_id="export_panel")
        
        self.export_png_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10, 10, 120, 40), text="PNG", manager=self.manager, container=self.export_panel)
        
        self.export_gif_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(140, 10, 120, 40), text="GIF", manager=self.manager, container=self.export_panel)
        
        self.save_project_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(10, 60, 120, 40), text="Save", manager=self.manager, container=self.export_panel)
        
        self.load_project_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(140, 60, 120, 40), text="Load", manager=self.manager, container=self.export_panel)
        
        self.undo_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(270, 60, 120, 40), text="Undo (Ctrl+Z)", manager=self.manager, container=self.export_panel)
        
        self.size_label = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(10, 110, 120, 30), text="Size:", manager=self.manager, container=self.export_panel)
        
        self.size_16_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(140, 110, 50, 30), text="16x16", manager=self.manager, container=self.export_panel)
        
        self.size_32_btn = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(200, 110, 50, 30), text="32x32", manager=self.manager, container=self.export_panel)
        
    def save_state(self):
        if len(self.history) > 20:
            self.history.pop(0)
        self.history.append(self.canvas_surface.copy())
        
    def undo(self):
        if len(self.history) > 1:
            self.history.pop()
            self.canvas_surface = self.history[-1].copy()
            self.frames[self.current_frame] = self.canvas_surface.copy()
            
    def get_pixel_pos(self, pos):
        x = (pos[0] - self.canvas_rect.x) // self.PIXEL_SIZE
        y = (pos[1] - self.canvas_rect.y) // self.PIXEL_SIZE
        return x, y
        
    def draw_pixel(self, x, y, color=None):
        if 0 <= x < self.CANVAS_SIZE and 0 <= y < self.CANVAS_SIZE:
            if color is None:
                color = self.current_color
            elif isinstance(color, tuple):
                color = pygame.Color(color)
                
            if self.current_tool == "erase":
                color = pygame.Color(255, 255, 255)
                
            rect = pygame.Rect(x * self.PIXEL_SIZE, y * self.PIXEL_SIZE, self.PIXEL_SIZE, self.PIXEL_SIZE)
            pygame.draw.rect(self.canvas_surface, color, rect)
            self.frames[self.current_frame] = self.canvas_surface.copy()
            
    def flood_fill(self, x, y, target_color, replacement_color):
        if target_color == replacement_color:
            return
        if not (0 <= x < self.CANVAS_SIZE and 0 <= y < self.CANVAS_SIZE):
            return
            
        if isinstance(target_color, pygame.Color):
            target_tuple = (target_color.r, target_color.g, target_color.b)
        else:
            target_tuple = target_color
            
        if isinstance(replacement_color, pygame.Color):
            replacement_tuple = (replacement_color.r, replacement_color.g, replacement_color.b)
        else:
            replacement_tuple = replacement_color
            
        stack = [(x, y)]
        while stack:
            x, y = stack.pop()
            if not (0 <= x < self.CANVAS_SIZE and 0 <= y < self.CANVAS_SIZE):
                continue
                
            pixel_color = self.canvas_surface.get_at((x * self.PIXEL_SIZE + self.PIXEL_SIZE // 2, y * self.PIXEL_SIZE + self.PIXEL_SIZE // 2))[:3]
            
            if pixel_color == target_tuple:
                self.draw_pixel(x, y, replacement_color)
                stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
                
    def draw_line(self, start, end):
        x1, y1 = start
        x2, y2 = end
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while True:
            self.draw_pixel(x1, y1)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
    
    def update_color_picker(self):
        temp_surface = pygame.Surface((46, 26))
        temp_surface.fill(self.current_color)
        pygame.draw.rect(temp_surface, (100, 100, 100), temp_surface.get_rect(), 2)
        
        self.color_picker.colours['normal_bg'] = self.current_color
        self.color_picker.colours['hovered_bg'] = self.current_color
        self.color_picker.colours['disabled_bg'] = self.current_color
        self.color_picker.colours['selected_bg'] = self.current_color
        self.color_picker.colours['active_bg'] = self.current_color
        
        self.color_picker.rebuild()
                
    def export_png(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pixel_art_{timestamp}.png"
        
        img = Image.new('RGB', (self.CANVAS_SIZE, self.CANVAS_SIZE), (255, 255, 255))
        
        for x in range(self.CANVAS_SIZE):
            for y in range(self.CANVAS_SIZE):
                pixel_color = self.canvas_surface.get_at((x * self.PIXEL_SIZE + self.PIXEL_SIZE // 2, y * self.PIXEL_SIZE + self.PIXEL_SIZE // 2))[:3]
                if pixel_color != (255, 255, 255):
                    img.putpixel((x, y), pixel_color)
        
        img = img.resize((self.CANVAS_SIZE * 10, self.CANVAS_SIZE * 10), Image.NEAREST)
        img.save(filename)
        print(f"Saved as: {filename}")
        
        self.show_message("Export", f"PNG saved as:\n{filename}")
        
    def export_gif(self):
        if len(self.frames) < 2:
            self.show_message("Error", "Minimum 2 frames required for GIF!")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"animation_{timestamp}.gif"
        
        images = []
        for frame in self.frames:
            img_str = pygame.image.tostring(frame, 'RGB')
            img = Image.frombytes('RGB', (self.CANVAS_WIDTH, self.CANVAS_WIDTH), img_str)
            
            small_img = Image.new('RGB', (self.CANVAS_SIZE, self.CANVAS_SIZE), (255, 255, 255))
            
            for x in range(self.CANVAS_SIZE):
                for y in range(self.CANVAS_SIZE):
                    pixel_color = frame.get_at((x * self.PIXEL_SIZE + self.PIXEL_SIZE // 2, y * self.PIXEL_SIZE + self.PIXEL_SIZE // 2))[:3]
                    if pixel_color != (255, 255, 255):
                        small_img.putpixel((x, y), pixel_color)
            
            scaled_img = small_img.resize((self.CANVAS_SIZE * 10, self.CANVAS_SIZE * 10), Image.NEAREST)
            images.append(scaled_img)
        
        images[0].save(filename, save_all=True, append_images=images[1:], duration=1000//self.animation_speed, loop=0)
        print(f"Animation saved as: {filename}")
        self.show_message("Export", f"GIF saved as:\n{filename}")
        
    def save_project(self):
        project = {
            "canvas_size": self.CANVAS_SIZE,
            "pixel_size": self.PIXEL_SIZE,
            "frames": [],
            "palette": self.current_palette
        }
        
        for frame in self.frames:
            frame_data = []
            for x in range(self.CANVAS_SIZE):
                row = []
                for y in range(self.CANVAS_SIZE):
                    color = frame.get_at((x * self.PIXEL_SIZE + self.PIXEL_SIZE // 2, y * self.PIXEL_SIZE + self.PIXEL_SIZE // 2))[:3]
                    row.append(list(color))
                frame_data.append(row)
            project["frames"].append(frame_data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"project_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(project, f, indent=2)
        print(f"Project saved: {filename}")
        self.show_message("Save", f"Project saved:\n{filename}")
        
    def load_project(self):
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        filename = filedialog.askopenfilename(title="Select project", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    project = json.load(f)
                
                if project["canvas_size"] != self.CANVAS_SIZE:
                    self.CANVAS_SIZE = project["canvas_size"]
                    self.PIXEL_SIZE = project["pixel_size"]
                    self.CANVAS_WIDTH = self.CANVAS_SIZE * self.PIXEL_SIZE
                    
                    self.canvas_surface = pygame.Surface((self.CANVAS_WIDTH, self.CANVAS_WIDTH))
                    self.canvas_rect = pygame.Rect(20, 20, self.CANVAS_WIDTH, self.CANVAS_WIDTH)
                
                self.frames = []
                for frame_data in project["frames"]:
                    frame_surface = pygame.Surface((self.CANVAS_WIDTH, self.CANVAS_WIDTH))
                    frame_surface.fill((255, 255, 255))
                    
                    for x, row in enumerate(frame_data):
                        for y, color in enumerate(row):
                            if color != [255, 255, 255]:
                                rect = pygame.Rect(x * self.PIXEL_SIZE, y * self.PIXEL_SIZE, self.PIXEL_SIZE, self.PIXEL_SIZE)
                                pygame.draw.rect(frame_surface, color, rect)
                    
                    self.frames.append(frame_surface)
                
                self.canvas_surface = self.frames[0].copy()
                self.current_frame = 0
                self.frame_label.set_text(f"Frame: {self.current_frame + 1}/{len(self.frames)}")
                
                if "palette" in project:
                    self.current_palette = project["palette"]
                    self.palette_dropdown.selected_option = self.current_palette
                
                self.history = [self.canvas_surface.copy()]
                print(f"Project loaded: {filename}")
                self.show_message("Load", f"Project loaded:\n{os.path.basename(filename)}")
                
            except Exception as e:
                print(f"Load error: {e}")
                self.show_message("Error", f"Failed to load project:\n{str(e)}")
                
    def show_message(self, title, message):
        message_rect = pygame.Rect(0, 0, 400, 200)
        message_rect.center = (self.WIDTH // 2, self.HEIGHT // 2)
        
        message_box = pygame_gui.windows.UIMessageWindow(rect=message_rect, window_title=title, html_message=message, manager=self.manager)
        
    def add_frame(self):
        new_frame = pygame.Surface((self.CANVAS_WIDTH, self.CANVAS_WIDTH))
        new_frame.fill((255, 255, 255))
        self.frames.append(new_frame)
        self.current_frame = len(self.frames) - 1
        self.canvas_surface = new_frame.copy()
        self.frame_label.set_text(f"Frame: {self.current_frame + 1}/{len(self.frames)}")
        self.save_state()
        
    def remove_frame(self):
        if len(self.frames) > 1:
            self.frames.pop(self.current_frame)
            if self.current_frame >= len(self.frames):
                self.current_frame = len(self.frames) - 1
            self.canvas_surface = self.frames[self.current_frame].copy()
            self.frame_label.set_text(f"Frame: {self.current_frame + 1}/{len(self.frames)}")
            self.save_state()
            
    def change_canvas_size(self, new_size):
        self.CANVAS_SIZE = new_size
        self.CANVAS_WIDTH = self.CANVAS_SIZE * self.PIXEL_SIZE
        
        self.canvas_surface = pygame.Surface((self.CANVAS_WIDTH, self.CANVAS_WIDTH))
        self.canvas_surface.fill((255, 255, 255))
        self.canvas_rect = pygame.Rect(20, 20, self.CANVAS_WIDTH, self.CANVAS_WIDTH)
        
        self.frames = [self.canvas_surface.copy()]
        self.current_frame = 0
        self.frame_label.set_text(f"Frame: {self.current_frame + 1}/{len(self.frames)}")
        self.history = [self.canvas_surface.copy()]
        
    def run(self):
        clock = pygame.time.Clock()
        running = True
        animation_timer = 0
        
        while running:
            time_delta = clock.tick(60) / 1000.0
            
            if self.is_animating and len(self.frames) > 1:
                animation_timer += time_delta
                if animation_timer >= 1.0 / self.animation_speed:
                    animation_timer = 0
                    self.current_frame = (self.current_frame + 1) % len(self.frames)
                    self.canvas_surface = self.frames[self.current_frame].copy()
                    self.frame_label.set_text(f"Frame: {self.current_frame + 1}/{len(self.frames)}")
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                self.manager.process_events(event)
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        self.undo()
                    elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        self.export_png()
                    elif event.key == pygame.K_LEFT:
                        if self.current_frame > 0:
                            self.current_frame -= 1
                            self.canvas_surface = self.frames[self.current_frame].copy()
                            self.frame_label.set_text(f"Frame: {self.current_frame + 1}/{len(self.frames)}")
                    elif event.key == pygame.K_RIGHT:
                        if self.current_frame < len(self.frames) - 1:
                            self.current_frame += 1
                            self.canvas_surface = self.frames[self.current_frame].copy()
                            self.frame_label.set_text(f"Frame: {self.current_frame + 1}/{len(self.frames)}")
                        
                if event.type == pygame.MOUSEBUTTONDOWN and self.canvas_rect.collidepoint(event.pos):
                    x, y = self.get_pixel_pos(event.pos)
                    
                    if self.current_tool == "brush":
                        self.is_drawing = True
                        self.draw_pixel(x, y)
                        self.save_state()
                        
                    elif self.current_tool == "fill":
                        target_color = self.canvas_surface.get_at((x * self.PIXEL_SIZE + self.PIXEL_SIZE // 2, y * self.PIXEL_SIZE + self.PIXEL_SIZE // 2))[:3]
                        self.flood_fill(x, y, target_color, self.current_color)
                        self.save_state()
                        
                    elif self.current_tool == "line":
                        self.is_drawing = True
                        self.last_pos = (x, y)
                        
                    elif self.current_tool == "erase":
                        self.is_drawing = True
                        self.draw_pixel(x, y)
                        self.save_state()
                        
                elif event.type == pygame.MOUSEMOTION and self.is_drawing:
                    if self.current_tool in ["brush", "erase"]:
                        x, y = self.get_pixel_pos(event.pos)
                        self.draw_pixel(x, y)
                        
                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.current_tool == "line" and self.is_drawing and self.last_pos:
                        x, y = self.get_pixel_pos(event.pos)
                        self.draw_line(self.last_pos, (x, y))
                        self.save_state()
                    self.is_drawing = False
                    self.last_pos = None
                    
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.brush_btn:
                        self.current_tool = "brush"
                    elif event.ui_element == self.fill_btn:
                        self.current_tool = "fill"
                    elif event.ui_element == self.line_btn:
                        self.current_tool = "line"
                    elif event.ui_element == self.erase_btn:
                        self.current_tool = "erase"
                    elif event.ui_element == self.color_picker:
                        import tkinter as tk
                        from tkinter import colorchooser
                        root = tk.Tk()
                        root.withdraw()
                        color_code = colorchooser.askcolor(title="Choose color")
                        if color_code[0]:
                            self.current_color = pygame.Color(color_code[0])
                            self.update_color_picker()
                    elif event.ui_element == self.export_png_btn:
                        self.export_png()
                    elif event.ui_element == self.export_gif_btn:
                        self.export_gif()
                    elif event.ui_element == self.save_project_btn:
                        self.save_project()
                    elif event.ui_element == self.load_project_btn:
                        self.load_project()
                    elif event.ui_element == self.undo_btn:
                        self.undo()
                    elif event.ui_element == self.add_frame_btn:
                        self.add_frame()
                    elif event.ui_element == self.remove_frame_btn:
                        self.remove_frame()
                    elif event.ui_element == self.play_anim_btn:
                        self.is_animating = not self.is_animating
                        self.play_anim_btn.set_text("⏸ Stop" if self.is_animating else "▶ Play")
                    elif event.ui_element == self.size_16_btn:
                        self.change_canvas_size(16)
                    elif event.ui_element == self.size_32_btn:
                        self.change_canvas_size(32)
                        
                if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    if event.ui_element == self.palette_dropdown:
                        self.current_palette = event.text
                        
                if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                    if event.ui_element == self.speed_slider:
                        self.animation_speed = int(event.value)
            
            self.manager.update(time_delta)
            
            self.screen.fill(self.BG_COLOR)
            
            self.screen.blit(self.canvas_surface, self.canvas_rect)
            
            if self.PIXEL_SIZE >= 4:
                for i in range(self.CANVAS_SIZE + 1):
                    pygame.draw.line(self.screen, self.GRID_COLOR, (self.canvas_rect.x + i * self.PIXEL_SIZE, self.canvas_rect.y), (self.canvas_rect.x + i * self.PIXEL_SIZE, self.canvas_rect.y + self.CANVAS_WIDTH), 1)
                    pygame.draw.line(self.screen, self.GRID_COLOR, (self.canvas_rect.x, self.canvas_rect.y + i * self.PIXEL_SIZE), (self.canvas_rect.x + self.CANVAS_WIDTH, self.canvas_rect.y + i * self.PIXEL_SIZE), 1)
            
            palette_x = self.CANVAS_WIDTH + 40
            palette_y = self.HEIGHT - 150
            pygame.draw.rect(self.screen, self.UI_BG_COLOR, (palette_x, palette_y, 400, 130))
            
            font = pygame.font.Font(None, 24)
            text = font.render("Palette:", True, (255, 255, 255))
            self.screen.blit(text, (palette_x + 10, palette_y + 10))
            
            colors = self.palettes[self.current_palette]
            for i, color in enumerate(colors):
                rect = pygame.Rect(palette_x + 10 + (i % 6) * 35, palette_y + 40 + (i // 6) * 35, 30, 30)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (100, 100, 100), rect, 1)
                
                mouse_pos = pygame.mouse.get_pos()
                if rect.collidepoint(mouse_pos):
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
                    if pygame.mouse.get_pressed()[0]:
                        self.current_color = pygame.Color(color)
                        self.update_color_picker()
            
            color_display = pygame.Rect(palette_x + 250, palette_y + 40, 60, 60)
            pygame.draw.rect(self.screen, self.current_color, color_display)
            pygame.draw.rect(self.screen, (200, 200, 200), color_display, 2)
            
            info_text = f"Tool: {self.current_tool} | Size: {self.CANVAS_SIZE}x{self.CANVAS_SIZE}"
            text = font.render(info_text, True, (200, 200, 200))
            self.screen.blit(text, (20, self.CANVAS_WIDTH + 30))
            
            hints = "Ctrl+Z: Undo | Arrows: Frames | LMB: Draw | RMB: Erase"
            hint_text = font.render(hints, True, (150, 150, 150))
            self.screen.blit(hint_text, (20, self.CANVAS_WIDTH + 60))
            
            self.manager.draw_ui(self.screen)
            
            pygame.display.flip()
            
        pygame.quit()

if __name__ == "__main__":
    editor = PixelArtEditor()
    editor.run()

#by AxonTechnologiess