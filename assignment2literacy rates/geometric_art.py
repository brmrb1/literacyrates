"""
Abstract Geometric Art Generator
Create dynamic abstract geometric art based on literacy rate data
"""

import pygame
import numpy as np
import json
import math
import time
from datetime import datetime
try:
    from pygame import gfxdraw
except ImportError:
    gfxdraw = None

class GeometricArtEngine:
    def __init__(self, width=1200, height=800):
        pygame.init()
        
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Abstract Geometric Art - Literacy Data Visualization")
        
        self.clock = pygame.time.Clock()
        self.background_color = (248, 250, 252)  # Minimalist white background
        
        # Initialize fonts - use system fonts to avoid encoding issues, support font weights
        try:
            self.font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 20)  # Microsoft YaHei
            self.small_font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 16)
            self.title_font = pygame.font.Font("C:/Windows/Fonts/msyhbd.ttc", 24)  # Microsoft YaHei Bold
            self.bold_font = pygame.font.Font("C:/Windows/Fonts/msyhbd.ttc", 18)  # Microsoft YaHei Bold Small
        except:
            # Fallback: use default font
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
            self.title_font = pygame.font.Font(None, 28)
            self.bold_font = pygame.font.Font(None, 22)
            self.small_font = pygame.font.Font(None, 18)
        
        # Animation time variables
        self.time = 0
        self.running = True
        self.paused = False
        
        # Geometric data
        self.geometric_entities = []
        self.stats = {}
        
        # FPS monitoring
        self.fps_counter = 0
        self.fps_timer = 0
        self.current_fps = 60
        
        # Global animation parameters
        self.global_scale = 1.0
        self.global_rotation = 0
        self.pulse_phase = 0
        
        # Performance optimizations - Caching
        self.color_cache = {}  # Cache computed colors
        self.surface_cache = {}  # Cache pre-rendered surfaces
        self.math_cache = {}  # Cache mathematical calculations
        self.blur_cache = {}  # Cache blurred surfaces
        self.cache_frame = 0  # Cache invalidation counter
        self.dirty_entities = set()  # Track entities needing re-render
        
        # 鼠标互动参数
        self.mouse_pos = (0, 0)
        self.mouse_influence_radius = 150
        self.mouse_force_strength = 0.5
        self.selected_entity = None
        self.show_info_panel = False  # Hide info panel by default
        
        # Click animation parameters
        self.click_scale_factor = 2.0  # Scale factor when clicked
        self.click_animation_duration = 60  # Animation duration in frames
        self.clicked_entities = {}  # Store clicked entity animation states
        
        # 数据对话框参数
        self.data_tooltip = {
            'visible': False,
            'entity': None,
            'position': (0, 0),
            'fade_timer': 0,
            'max_fade_time': 180  # 3秒后淡出
        }
        
        # 提示框信息
        self.tooltip_info = None
        
    def draw_rounded_rect(self, surface, color, rect, radius):
        """绘制圆角矩形"""
        x, y, width, height = rect
        
        # 确保半径不超过矩形尺寸的一半
        radius = min(radius, width // 2, height // 2)
        
        # 绘制矩形的各个部分
        # 中央矩形
        pygame.draw.rect(surface, color, (x + radius, y, width - 2 * radius, height))
        pygame.draw.rect(surface, color, (x, y + radius, width, height - 2 * radius))
        
        # 四个角的圆形
        pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
        pygame.draw.circle(surface, color, (x + width - radius, y + radius), radius)
        pygame.draw.circle(surface, color, (x + radius, y + height - radius), radius)
        pygame.draw.circle(surface, color, (x + width - radius, y + height - radius), radius)
        
    def draw_rounded_rect_outline(self, surface, color, rect, radius, width=1):
        """绘制圆角矩形轮廓"""
        x, y, w, h = rect
        radius = min(radius, w // 2, h // 2)
        
        # 绘制四条边
        pygame.draw.line(surface, color, (x + radius, y), (x + w - radius, y), width)  # 上边
        pygame.draw.line(surface, color, (x + radius, y + h), (x + w - radius, y + h), width)  # 下边
        pygame.draw.line(surface, color, (x, y + radius), (x, y + h - radius), width)  # 左边
        pygame.draw.line(surface, color, (x + w, y + radius), (x + w, y + h - radius), width)  # 右边
        
        # 绘制四个圆角
        pygame.draw.circle(surface, color, (x + radius, y + radius), radius, width)
        pygame.draw.circle(surface, color, (x + w - radius, y + radius), radius, width)
        pygame.draw.circle(surface, color, (x + radius, y + h - radius), radius, width)
        pygame.draw.circle(surface, color, (x + w - radius, y + h - radius), radius, width)
        
    def load_data(self):
        """加载几何数据"""
        try:
            with open('geometric_data.json', 'r', encoding='utf-8') as f:
                self.geometric_entities = json.load(f)
            
            with open('geometric_stats.json', 'r', encoding='utf-8') as f:
                self.stats = json.load(f)
            
            print(f"✅ Loaded {len(self.geometric_entities)} geometric entities")
            return True
            
        except FileNotFoundError:
            print("❌ Geometric data files not found, please run geometric_processor.py first")
            return False
    
    def hsl_to_rgb(self, hue, saturation, lightness):
        """HSL to RGB color conversion - optimized for white background with caching"""
        # Create cache key
        cache_key = (round(hue, 1), round(saturation, 3), round(lightness, 3))
        if cache_key in self.color_cache:
            return self.color_cache[cache_key]
        
        hue = hue % 360
        h = hue / 360
        s = saturation
        # Adjust lightness for white background - reduce brightness for visibility
        l = min(lightness * 0.6, 0.7)  # Limit max lightness to 0.7, reduce overall by 40%
        
        if s == 0:
            r = g = b = l
        else:
            def hue_to_rgb(p, q, t):
                if t < 0:
                    t += 1
                if t > 1:
                    t -= 1
                if t < 1/6:
                    return p + (q - p) * 6 * t
                if t < 1/2:
                    return q
                if t < 2/3:
                    return p + (q - p) * (2/3 - t) * 6
                return p
            
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)
        
        result = int(r * 255), int(g * 255), int(b * 255)
        self.color_cache[cache_key] = result
        return result
    
    def get_macaron_color(self, hue, literacy_rate):
        """生成增强鲜艳度的马卡龙配色方案 - 带缓存优化"""
        # Create cache key for colors
        cache_key = (round(hue, 1), round(literacy_rate, 1))
        if cache_key in self.color_cache:
            return self.color_cache[cache_key]
        
        # 基于识字率调整颜色深度，整体大幅提升饱和度
        if literacy_rate >= 90:
            saturation, lightness = 0.95, 0.72
        elif literacy_rate >= 70:
            saturation, lightness = 0.92, 0.68
        elif literacy_rate >= 50:
            saturation, lightness = 0.88, 0.63
        else:
            saturation, lightness = 0.85, 0.58
        
        # 调整特定色相的马卡龙效果，大幅增强鲜艳度
        if 0 <= hue < 60:  # 红橙色系
            saturation *= 1.08
        elif 60 <= hue < 120:  # 黄绿色系
            lightness *= 1.03
            saturation *= 1.06
        elif 120 <= hue < 180:  # 绿青色系
            saturation *= 1.05
        elif 180 <= hue < 240:  # 青蓝色系
            saturation *= 1.07
        elif 240 <= hue < 300:  # 蓝紫色系
            saturation *= 1.12
        else:  # 紫红色系
            saturation *= 1.10
        
        # 确保值在合理范围内，允许更高的饱和度
        saturation = max(0.6, min(1.0, saturation))
        lightness = max(0.45, min(0.85, lightness))
        
        result = self.hsl_to_rgb(hue, saturation, lightness)
        self.color_cache[cache_key] = result
        return result
    
    def calculate_clarity(self, literacy_rate):
        """根据识字率计算清晰度参数"""
        # 识字率映射到清晰度 (0.3-1.0范围)
        # 高识字率 = 高清晰度，低识字率 = 低清晰度（模糊）
        clarity = 0.3 + (literacy_rate / 100) * 0.7
        return clarity
    
    def apply_blur_effect(self, surface, blur_radius):
        """应用模糊效果 - 优化缓存版本"""
        if blur_radius <= 1:
            return surface
        
        # Create cache key
        surface_id = id(surface)
        cache_key = (surface_id, int(blur_radius * 10))
        
        if cache_key in self.blur_cache:
            return self.blur_cache[cache_key]
        
        # Simplified and faster blur - use transparency instead of pixel-level blur
        width, height = surface.get_size()
        blurred_surface = surface.copy()
        
        # Apply transparency-based blur effect (much faster)
        blur_alpha = max(50, 255 - int(blur_radius * 40))
        alpha_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        alpha_surface.fill((255, 255, 255, blur_alpha))
        blurred_surface.blit(alpha_surface, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
        
        # Cache the result (limit cache size)
        if len(self.blur_cache) > 50:
            # Clear oldest entries
            keys_to_remove = list(self.blur_cache.keys())[:25]
            for key in keys_to_remove:
                del self.blur_cache[key]
        
        self.blur_cache[cache_key] = blurred_surface
        return blurred_surface
    
    def create_clarity_surface(self, entity, base_surface):
        """根据识字率创建清晰度调整后的surface"""
        literacy_rate = entity['literacy_rate']
        clarity = self.calculate_clarity(literacy_rate)
        
        # 计算模糊半径 (识字率越低，模糊越强)
        blur_radius = (1 - clarity) * 8  # 0-8像素的模糊范围
        
        if blur_radius > 1:
            # 应用模糊效果
            blurred_surface = self.apply_blur_effect(base_surface, blur_radius)
            
            # 混合原图和模糊图
            final_surface = pygame.Surface(base_surface.get_size(), pygame.SRCALPHA)
            final_surface.blit(blurred_surface, (0, 0))
            
            # 根据清晰度调整整体透明度
            clarity_alpha = int(clarity * 255)
            temp_surface = pygame.Surface(base_surface.get_size(), pygame.SRCALPHA)
            temp_surface.fill((255, 255, 255, clarity_alpha))
            final_surface.blit(temp_surface, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
            
            return final_surface
        else:
            return base_surface
    
    def draw_circle(self, surface, entity, x, y, size):
        """绘制圆形 - 使用马卡龙配色，优化缓存版本"""
        # Create cache key for this entity's visual state
        entity_key = f"{entity['entity']}_{entity['pattern']}_{int(size)}_{int(entity['opacity']*100)}"
        click_scale = self.get_entity_click_scale(entity)
        mouse_influenced = entity.get('mouse_influenced', False)
        
        # Check if we can use cached surface
        cache_key = (entity_key, int(click_scale*100), mouse_influenced)
        
        if cache_key not in self.surface_cache:
            # 使用马卡龙配色方案
            color = self.get_macaron_color(entity['hue'], entity['literacy_rate'])
            opacity = int(entity['opacity'] * 255)
            
            # 根据识字率调整清晰度
            clarity = self.calculate_clarity(entity['literacy_rate'])
            
            # 应用点击放大效果
            final_size = size * click_scale
            
            # 鼠标互动增强效果
            if mouse_influenced:
                influence = entity.get('influence_strength', 0)
                final_size = final_size * (1 + influence * 0.3)
                opacity = min(255, int(opacity * (1 + influence * 0.5)))
                clarity = min(1.0, clarity + influence * 0.3)
            
            # 创建临时surface用于绘制
            temp_size = int(final_size * 2) + 20
            temp_surface = pygame.Surface((temp_size, temp_size), pygame.SRCALPHA)
            center_offset = temp_size // 2
            
            # 调整透明度基于清晰度
            adjusted_opacity = int(opacity * clarity)
            
            # Simplified pattern rendering for better performance
            if entity['pattern'] in ['solid', 'gradient']:  # Combine for efficiency
                pygame.draw.circle(temp_surface, (*color, adjusted_opacity), (center_offset, center_offset), int(final_size))
            elif entity['pattern'] == 'outline':
                line_width = max(3, int(6 * clarity))
                pygame.draw.circle(temp_surface, (*color, adjusted_opacity), (center_offset, center_offset), int(final_size), line_width)
            elif entity['pattern'] == 'dotted':
                # Pre-calculate dot positions for better performance
                dot_count = max(6, int(12 * clarity))
                angle_step = 360 // dot_count
                dot_size = max(1, int(3 * clarity))
                for i in range(0, 360, angle_step):
                    angle_rad = math.radians(i)
                    dot_x = center_offset + math.cos(angle_rad) * final_size * 0.7
                    dot_y = center_offset + math.sin(angle_rad) * final_size * 0.7
                    pygame.draw.circle(temp_surface, (*color, adjusted_opacity), (int(dot_x), int(dot_y)), dot_size)
            
            # 应用基于识字率的模糊效果（简化）
            if clarity < 0.9:
                blur_radius = (1 - clarity) * 4
                temp_surface = self.apply_blur_effect(temp_surface, blur_radius)
            
            # Cache the surface (limit cache size)
            if len(self.surface_cache) > 100:
                # Clear some old entries
                keys_to_remove = list(self.surface_cache.keys())[:50]
                for key in keys_to_remove:
                    del self.surface_cache[key]
            
            self.surface_cache[cache_key] = (temp_surface, temp_size // 2)
        
        # Use cached surface
        cached_surface, center_offset = self.surface_cache[cache_key]
        
        # 选中状态效果（不缓存，因为是临时状态）
        if entity == self.selected_entity:
            pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), int(size * click_scale + 8), 3)
        
        surface.blit(cached_surface, (x - center_offset, y - center_offset))
    
    def draw_polygon(self, surface, entity, x, y, size, sides):
        """绘制多边形 - 使用马卡龙配色，优化缓存版本"""
        # Create cache key for this entity's visual state
        rotation_key = int((entity['rotation'] + self.global_rotation) / 10) * 10  # Round to 10 degrees
        entity_key = f"{entity['entity']}_{entity['pattern']}_{sides}_{int(size)}_{rotation_key}"
        click_scale = self.get_entity_click_scale(entity)
        mouse_influenced = entity.get('mouse_influenced', False)
        
        cache_key = (entity_key, int(click_scale*100), mouse_influenced)
        
        if cache_key not in self.surface_cache:
            # 使用马卡龙配色方案
            color = self.get_macaron_color(entity['hue'], entity['literacy_rate'])
            opacity = int(entity['opacity'] * 255)
            
            # 根据识字率调整清晰度
            clarity = self.calculate_clarity(entity['literacy_rate'])
            
            final_size = size * click_scale
            
            # 鼠标互动增强效果
            if mouse_influenced:
                influence = entity.get('influence_strength', 0)
                final_size = final_size * (1 + influence * 0.3)
                opacity = min(255, int(opacity * (1 + influence * 0.5)))
                clarity = min(1.0, clarity + influence * 0.3)
            
            # Pre-calculate polygon vertices (optimized)
            angle_step = 2 * math.pi / sides
            rotation = math.radians(entity['rotation'] + self.global_rotation)
            
            # 创建临时surface用于绘制
            temp_size = int(final_size * 3) + 20
            temp_surface = pygame.Surface((temp_size, temp_size), pygame.SRCALPHA)
            center_offset = temp_size // 2
            
            # Calculate points relative to center
            temp_points = []
            for i in range(sides):
                angle = i * angle_step + rotation
                point_x = center_offset + math.cos(angle) * final_size
                point_y = center_offset + math.sin(angle) * final_size
                temp_points.append((point_x, point_y))
            
            # 调整透明度基于清晰度
            adjusted_opacity = int(opacity * clarity)
            
            # Simplified pattern rendering
            if entity['pattern'] in ['solid', 'gradient', 'striped']:  # Combine for efficiency
                pygame.draw.polygon(temp_surface, (*color, adjusted_opacity), temp_points)
            elif entity['pattern'] == 'outline':
                line_width = max(3, int(6 * clarity))
                pygame.draw.polygon(temp_surface, (*color, adjusted_opacity), temp_points, line_width)
            
            # 应用基于识字率的模糊效果（简化）
            if clarity < 0.9:
                blur_radius = (1 - clarity) * 4
                temp_surface = self.apply_blur_effect(temp_surface, blur_radius)
            
            # Cache management
            if len(self.surface_cache) > 100:
                keys_to_remove = list(self.surface_cache.keys())[:50]
                for key in keys_to_remove:
                    del self.surface_cache[key]
            
            self.surface_cache[cache_key] = (temp_surface, center_offset)
        
        # Use cached surface
        cached_surface, center_offset = self.surface_cache[cache_key]
        
        # 选中状态效果（不缓存）
        if entity == self.selected_entity:
            pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), int(size * click_scale + 8), 3)
        
        surface.blit(cached_surface, (x - center_offset, y - center_offset))
    
    def update_entity_position(self, entity):
        """更新实体位置 - 优化数学计算"""
        if not self.paused:
            # Cache frequently used values
            delta_time = self.clock.get_time() * 0.001  # Convert to seconds directly
            frame_factor = delta_time * 60  # Pre-calculate frame factor
            
            # 进一步降低基础位移速度，让移动极其优雅
            base_movement_factor = 0.0015 * frame_factor
            entity['x'] += entity['velocity']['x'] * base_movement_factor
            entity['y'] += entity['velocity']['y'] * base_movement_factor
            
            # Pre-calculate oscillation values for better performance
            time_factor = self.time * 0.001
            freq_time = time_factor * entity['frequency']
            phase = entity['phase']
            
            # Cache sin/cos calculations
            cache_key = (int(freq_time * 100), int(phase * 100))
            if cache_key not in self.math_cache:
                self.math_cache[cache_key] = (
                    math.sin(freq_time + phase),
                    math.cos(freq_time * 1.3 + phase)
                )
                
                # Limit cache size
                if len(self.math_cache) > 200:
                    # Remove half of the cache entries
                    keys_to_remove = list(self.math_cache.keys())[:100]
                    for key in keys_to_remove:
                        del self.math_cache[key]
            
            oscillation_x, oscillation_y = self.math_cache[cache_key]
            oscillation_x *= entity['oscillation_amplitude']
            oscillation_y *= entity['oscillation_amplitude']
            
            # 振荡运动也使用帧时间插值，进一步降低速度
            oscillation_factor = 0.001 * frame_factor
            entity['x'] += oscillation_x * oscillation_factor
            entity['y'] += oscillation_y * oscillation_factor
            
            # 鼠标互动力场
            self.apply_mouse_interaction(entity)
            
            # 添加轻微的速度衰减让移动更自然
            damping_factor = 0.999
            entity['velocity']['x'] *= damping_factor
            entity['velocity']['y'] *= damping_factor
            
            # 改进边界检测和反弹
            margin = 0.02
            if entity['x'] < margin or entity['x'] > 0.98:  # Pre-calculate 1-margin
                entity['velocity']['x'] *= -0.8
                entity['x'] = max(margin, min(0.98, entity['x']))
            
            if entity['y'] < margin or entity['y'] > 0.98:
                entity['velocity']['y'] *= -0.8
                entity['y'] = max(margin, min(0.98, entity['y']))
            
            # 更新旋转，使用帧时间插值
            entity['rotation'] += entity['angular_velocity'] * frame_factor
            if entity['rotation'] >= 360:
                entity['rotation'] -= 360
            elif entity['rotation'] < 0:
                entity['rotation'] += 360
    
    def apply_mouse_interaction(self, entity):
        """应用鼠标互动效果 - 优化计算"""
        # Early exit if mouse is at origin (not moved yet)
        if self.mouse_pos[0] <= 0 or self.mouse_pos[1] <= 0:
            entity['mouse_influenced'] = False
            entity['influence_strength'] = 0
            return
        
        # Pre-calculate entity screen position
        entity_x = entity['x'] * self.width
        entity_y = entity['y'] * self.height
        
        # Fast distance check using squared distance first (avoid sqrt when possible)
        dx = self.mouse_pos[0] - entity_x
        dy = self.mouse_pos[1] - entity_y
        distance_squared = dx*dx + dy*dy
        influence_radius_squared = self.mouse_influence_radius * self.mouse_influence_radius
        
        if distance_squared < influence_radius_squared and distance_squared > 0:
            # Only calculate sqrt when needed
            distance = math.sqrt(distance_squared)
            
            # 计算影响强度（使用平滑曲线）
            normalized_distance = distance / self.mouse_influence_radius
            # 使用平滑的三次函数而不是线性
            influence = (1 - normalized_distance) ** 1.5 * self.mouse_force_strength
            
            # 归一化方向向量
            inv_distance = 1.0 / distance  # Avoid division in next two lines
            dx_norm = dx * inv_distance
            dy_norm = dy * inv_distance
            
            # Pre-calculated interaction factor
            delta_time = self.clock.get_time() * 0.001  # Convert directly
            interaction_factor = 0.15 * delta_time * 60
            
            # 应用平滑的吸引力
            force_x = dx_norm * influence * interaction_factor
            force_y = dy_norm * influence * interaction_factor
            entity['velocity']['x'] += force_x
            entity['velocity']['y'] += force_y
            
            # 限制最大速度，防止过度加速
            vel_x, vel_y = entity['velocity']['x'], entity['velocity']['y']
            velocity_squared = vel_x*vel_x + vel_y*vel_y
            max_velocity_squared = 9.0  # 3.0^2
            
            if velocity_squared > max_velocity_squared:
                scale_factor = 3.0 / math.sqrt(velocity_squared)  # max_velocity / magnitude
                entity['velocity']['x'] *= scale_factor
                entity['velocity']['y'] *= scale_factor
            
            # 增强视觉效果
            entity['mouse_influenced'] = True
            entity['influence_strength'] = influence
        else:
            entity['mouse_influenced'] = False
            entity['influence_strength'] = 0
    
    def update_click_animations(self):
        """更新点击动画效果"""
        entities_to_remove = []
        
        for entity_id, anim_data in self.clicked_entities.items():
            # 使用帧时间进行平滑插值
            delta_time = self.clock.get_time() / 1000.0
            anim_data['frame'] += delta_time * 60  # 60FPS基准
            
            # 计算动画进度 (0-1)
            progress = anim_data['frame'] / self.click_animation_duration
            
            if progress >= 1.0:
                entities_to_remove.append(entity_id)
            else:
                # 使用更平滑的三次贝塞尔缓动函数
                if progress < 0.4:  # 前40%时间放大
                    # 缓动进入
                    t = progress / 0.4
                    eased_t = t * t * (3 - 2 * t)  # 平滑步函数
                    scale = 1.0 + (self.click_scale_factor - 1.0) * eased_t
                else:  # 后60%时间缓慢缩回
                    remaining_progress = (progress - 0.4) / 0.6
                    # 缓动退出
                    eased_t = 1 - (1 - remaining_progress) ** 2  # 二次缓出
                    scale = self.click_scale_factor - (self.click_scale_factor - 1.0) * eased_t
                
                anim_data['scale'] = scale
        
        # 移除完成的动画
        for entity_id in entities_to_remove:
            del self.clicked_entities[entity_id]
    
    def get_entity_click_scale(self, entity):
        """获取实体的点击缩放因子"""
        entity_id = f"{entity['entity']}_{entity['literacy_rate']}"
        if entity_id in self.clicked_entities:
            return self.clicked_entities[entity_id]['scale']
        return 1.0
    
    def get_entity_at_position(self, pos):
        """获取指定位置的实体"""
        for entity in self.geometric_entities:
            entity_x = entity['x'] * self.width
            entity_y = entity['y'] * self.height
            base_size = entity['size'] * 30 * self.global_scale
            dynamic_size = base_size * entity['scale_factor']
            
            dx = pos[0] - entity_x
            dy = pos[1] - entity_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance <= dynamic_size:
                return entity
        return None
    
    def draw_background_patterns(self):
        """绘制背景几何图案 - 已简化为极简风格"""
        # 极简主义：移除所有背景装饰元素
        pass
    
    def apply_global_effects(self):
        """应用全局视觉效果 - 优化版本"""
        if not self.paused:
            # 全局脉冲效果 - 减少计算频率
            self.pulse_phase += 0.01
            # Cache sin calculation result
            pulse_key = int(self.pulse_phase * 100) % 628  # 2*pi*100
            if pulse_key not in self.math_cache:
                self.math_cache[pulse_key] = math.sin(self.pulse_phase)
            self.global_scale = 1.0 + 0.1 * self.math_cache[pulse_key]
            
            # 全局旋转 - 减少增量计算
            self.global_rotation += 0.2
            if self.global_rotation >= 360:
                self.global_rotation -= 360
        
    def draw_info_panel(self):
        """绘制极简主义信息面板"""
        if not self.show_info_panel:
            return
        
        # 极简主义面板设计 - 优化尺寸适应增强间距
        panel_width = 360  # 增加宽度确保长文字不超出
        panel_height = 300  # 增加高度适应新的行间距设置
        corner_radius = 18  # 增加圆角半径，让弧形更明显
        padding = 20
        
        # 创建面板表面
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        
        # 极简白色背景，微妙阴影效果
        bg_color = (255, 255, 255, 245)  # 半透明白色
        shadow_color = (0, 0, 0, 20)    # 轻微阴影
        
        # 绘制阴影 (轻微偏移) - 弧形圆角设计
        shadow_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        self.draw_rounded_rect(shadow_surface, shadow_color, 
                              (2, 2, panel_width-2, panel_height-2), corner_radius)
        self.screen.blit(shadow_surface, (8, 8))
        
        # 绘制主面板 - 弧形圆角设计
        self.draw_rounded_rect(panel_surface, bg_color, 
                              (0, 0, panel_width, panel_height), corner_radius)
        
        # 微妙边框 - 弧形圆角设计，淡蓝色加粗边框
        border_color = (173, 216, 230, 180)  # 淡蓝色边框 (Light Blue)
        self.draw_rounded_rect_outline(panel_surface, border_color, 
                                     (0, 0, panel_width, panel_height), corner_radius, 3)  # 加粗到3像素
        
        self.screen.blit(panel_surface, (10, 10))
        
        # 文字内容 - 极简主义层次设计
        y_offset = 10 + padding
        
        # 主标题 - 最高层次，粗体大字
        title_color = (45, 55, 70)  # 深灰蓝色
        title = self.title_font.render("Geometric Art", True, title_color)
        self.screen.blit(title, (10 + padding, y_offset))
        y_offset += 38  # 增加标题后间距
        
        # 副标题 - 数据可视化说明
        subtitle_color = (120, 130, 140)
        subtitle = self.small_font.render("UNESCO Literacy Data Visualization", True, subtitle_color)
        self.screen.blit(subtitle, (10 + padding, y_offset))
        y_offset += 30  # 增加副标题后间距，为分组预留空间
        
        # 统计数据区域
        if self.stats:
            # 分组标题 - 增加分组间距
            stats_title_color = (70, 80, 90)
            stats_title = self.bold_font.render("Statistics", True, stats_title_color)
            self.screen.blit(stats_title, (10 + padding, y_offset))
            y_offset += 26  # 增加分组标题后间距
            
            # 统计数据 - 使用数据颜色编码，增加行间距
            entity_count_color = (100, 120, 140)
            entity_text = self.small_font.render(f"Entities: {self.stats['total_entities']}", True, entity_count_color)
            self.screen.blit(entity_text, (10 + padding + 10, y_offset))
            y_offset += 22  # 增加行间距
            
            avg_literacy = self.stats['literacy_statistics']['mean']
            # 根据平均识字率选择颜色
            if avg_literacy >= 80:
                literacy_color = (76, 175, 80)  # 绿色
            elif avg_literacy >= 60:
                literacy_color = (255, 152, 0)  # 橙色
            else:
                literacy_color = (244, 67, 54)  # 红色
                
            literacy_text = self.small_font.render(f"Avg Literacy: {avg_literacy:.1f}%", True, literacy_color)
            self.screen.blit(literacy_text, (10 + padding + 10, y_offset))
            y_offset += 32  # 增加分组结束后的间距
        
        # FPS显示 - 性能监控
        fps_title_color = (70, 80, 90)
        fps_title = self.bold_font.render("Performance", True, fps_title_color)
        self.screen.blit(fps_title, (10 + padding, y_offset))
        y_offset += 26
        
        # 当前FPS - 实时显示
        fps_color = (76, 175, 80) if self.current_fps >= 50 else (255, 152, 0) if self.current_fps >= 30 else (244, 67, 54)
        fps_text = self.small_font.render(f"FPS: {self.current_fps:.0f}", True, fps_color)
        self.screen.blit(fps_text, (10 + padding + 10, y_offset))
        y_offset += 32
        
        # 选中实体信息
        if self.selected_entity:
            # 分组标题 - 增加分组间距
            selected_title_color = (70, 80, 90)
            selected_title = self.bold_font.render("Selected Entity", True, selected_title_color)
            self.screen.blit(selected_title, (10 + padding, y_offset))
            y_offset += 26  # 增加分组标题后间距
            
            # 实体名称 - 主要信息，粗体
            entity_name = self.selected_entity['entity']
            if len(entity_name) > 22:  # 增加允许的字符数以适应更宽面板
                entity_name = entity_name[:19] + "..."
            
            name_color = (45, 55, 70)
            name_text = self.bold_font.render(entity_name, True, name_color)
            self.screen.blit(name_text, (10 + padding + 10, y_offset))
            y_offset += 24  # 增加实体名称后的行间距
            
            # 识字率 - 关键数据，彩色显示
            literacy_rate = self.selected_entity['literacy_rate']
            if literacy_rate >= 90:
                rate_color = (76, 175, 80)
            elif literacy_rate >= 70:
                rate_color = (255, 152, 0)
            else:
                rate_color = (244, 67, 54)
                
            rate_text = self.font.render(f"{literacy_rate:.1f}%", True, rate_color)
            self.screen.blit(rate_text, (10 + padding + 10, y_offset))
            
            # 识字率标签
            rate_label = self.small_font.render("Literacy Rate", True, (120, 130, 140))
            self.screen.blit(rate_label, (10 + padding + 10 + rate_text.get_width() + 8, y_offset + 3))
            y_offset += 28  # 增加识字率后的行间距
            
            # 形状信息 - 次要信息，普通字体
            shape_color = (120, 130, 140)
            shape_text = self.small_font.render(f"Shape: {self.selected_entity['shape'].title()}", True, shape_color)
            self.screen.blit(shape_text, (10 + padding + 10, y_offset))
        
        # 控制说明 - 底部，最低层次，适应新的面板高度
        control_y = 10 + panel_height - 30  # 调整位置适应300px高度
        control_color = (150, 160, 170)
        control_text = self.small_font.render("H-面板 | ESC-退出 | 点击-选择", True, control_color)
        self.screen.blit(control_text, (10 + padding, control_y))
    
    def save_screenshot(self):
        """Save screenshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"geometric_art_{timestamp}.png"
        pygame.image.save(self.screen, filename)
        print(f"📸 Screenshot saved: {filename}")
    
    def handle_events(self):
        """Handle events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                    print(f"Animation {'paused' if self.paused else 'resumed'}")
                elif event.key == pygame.K_s:
                    self.save_screenshot()
                elif event.key == pygame.K_h:
                    self.show_info_panel = not self.show_info_panel
                    print(f"Info panel {'shown' if self.show_info_panel else 'hidden'}")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    clicked_entity = self.get_entity_at_position(event.pos)
                    if clicked_entity:
                        # 触发点击动画
                        entity_id = f"{clicked_entity['entity']}_{clicked_entity['literacy_rate']}"
                        self.clicked_entities[entity_id] = {
                            'start_time': time.time(),
                            'entity': clicked_entity,
                            'frame': 0,
                            'scale': 1.0
                        }
                        
                        # 计算几何体在屏幕上的位置
                        entity_screen_x = clicked_entity['x'] * self.width
                        entity_screen_y = clicked_entity['y'] * self.height
                        
                        # Show data tooltip next to the geometry
                        self.show_data_tooltip(clicked_entity, (entity_screen_x, entity_screen_y))
                        self.selected_entity = clicked_entity
                        print(f"Selected entity: {clicked_entity['entity']} (Literacy rate: {clicked_entity['literacy_rate']:.1f}%)")
                    else:
                        # Click on empty area, hide tooltip
                        self.data_tooltip['visible'] = False
                        self.selected_entity = None
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
    
    def render_frame(self):
        """渲染一帧 - 优化版本"""
        # 清空屏幕
        self.screen.fill(self.background_color)
        
        # 绘制背景图案 - 已移除以提高性能
        # self.draw_background_patterns()  # Disabled for performance
        
        # 应用全局效果
        self.apply_global_effects()
        
        # 绘制所有几何实体 - 优化循环
        width, height = self.width, self.height  # Cache dimensions
        global_scale = self.global_scale  # Cache global scale
        
        for entity in self.geometric_entities:
            # 更新位置
            self.update_entity_position(entity)
            
            # 计算屏幕坐标 - 优化计算
            screen_x = entity['x'] * width
            screen_y = entity['y'] * height
            
            # 计算动态大小 - 预计算
            dynamic_size = entity['size'] * 30 * global_scale * entity['scale_factor']
            
            # 根据形状绘制 - 优化分支
            shape = entity['shape']
            if shape == 'circle':
                self.draw_circle(self.screen, entity, screen_x, screen_y, dynamic_size)
            elif shape == 'triangle':
                self.draw_polygon(self.screen, entity, screen_x, screen_y, dynamic_size, 3)
            elif shape == 'square':
                self.draw_polygon(self.screen, entity, screen_x, screen_y, dynamic_size, 4)
            elif shape == 'pentagon':
                self.draw_polygon(self.screen, entity, screen_x, screen_y, dynamic_size, 5)
            elif shape == 'hexagon':
                self.draw_polygon(self.screen, entity, screen_x, screen_y, dynamic_size, 6)
        
        # 绘制鼠标影响区域指示器 - 仅在需要时绘制
        if self.mouse_pos[0] > 0 and self.mouse_pos[1] > 0 and self.current_fps > 30:
            self.draw_mouse_influence_indicator()
        
        # 绘制数据提示框
        if self.data_tooltip['visible']:
            self.draw_data_tooltip()
        
        # 更新显示
        pygame.display.flip()
    
    def draw_mouse_influence_indicator(self):
        """绘制鼠标影响区域指示器 - 优化版本"""
        # Cache the influence surface to avoid recreating every frame
        cache_key = "mouse_influence_indicator"
        if cache_key not in self.surface_cache:
            # Create cached influence surface
            influence_surface = pygame.Surface((self.mouse_influence_radius * 2, self.mouse_influence_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(influence_surface, (100, 100, 255, 30), 
                             (self.mouse_influence_radius, self.mouse_influence_radius), 
                             self.mouse_influence_radius)
            pygame.draw.circle(influence_surface, (100, 100, 255, 80), 
                             (self.mouse_influence_radius, self.mouse_influence_radius), 
                             self.mouse_influence_radius, 2)
            self.surface_cache[cache_key] = influence_surface
        
        # Use cached surface
        influence_surface = self.surface_cache[cache_key]
        self.screen.blit(influence_surface, 
                       (self.mouse_pos[0] - self.mouse_influence_radius, 
                        self.mouse_pos[1] - self.mouse_influence_radius))
    
    def draw_data_tooltip(self):
        """绘制数据对话框"""
        if not self.data_tooltip['visible'] or not self.data_tooltip['entity']:
            return
        
        entity = self.data_tooltip['entity']
        x, y = self.data_tooltip['position']
        
        # 计算淡出透明度
        fade_progress = min(1.0, self.data_tooltip['fade_timer'] / self.data_tooltip['max_fade_time'])
        if fade_progress > 0.7:  # 70%后开始淡出
            alpha_factor = 1.0 - (fade_progress - 0.7) / 0.3
        else:
            alpha_factor = 1.0
        
        # 对话框尺寸和位置 - 极简主义设计，优化弧形圆角
        tooltip_width = 280
        tooltip_height = 140
        corner_radius = 16  # 增加圆角半径，让弧形更优雅
        
        # 获取几何体的大小以计算偏移
        entity = self.data_tooltip['entity']
        base_size = entity['size'] * 30 * self.global_scale
        
        # 智能选择提示框位置：避免与其他几何体重叠
        entity = self.data_tooltip['entity']
        base_size = entity['size'] * 30 * self.global_scale
        
        # 计算多个候选位置
        candidates = [
            # 右侧位置
            (x + base_size + 30, y - tooltip_height // 2, 'left'),
            # 左侧位置  
            (x - tooltip_width - base_size - 30, y - tooltip_height // 2, 'right'),
            # 上方位置
            (x - tooltip_width // 2, y - tooltip_height - base_size - 30, 'bottom'),
            # 下方位置
            (x - tooltip_width // 2, y + base_size + 30, 'top')
        ]
        
        # 选择最佳位置：在屏幕内且与其他几何体重叠最少
        best_candidate = None
        min_overlap = float('inf')
        
        for candidate_x, candidate_y, triangle_side in candidates:
            # 检查是否在屏幕范围内
            if (candidate_x < 10 or candidate_x + tooltip_width > self.width - 10 or
                candidate_y < 10 or candidate_y + tooltip_height > self.height - 10):
                continue
            
            # 计算与其他几何体的重叠度
            overlap_count = 0
            tooltip_rect = pygame.Rect(candidate_x, candidate_y, tooltip_width, tooltip_height)
            
            for other_entity in self.geometric_entities:
                if other_entity == entity:  # 跳过自身
                    continue
                    
                other_x = other_entity['x'] * self.width
                other_y = other_entity['y'] * self.height
                other_size = other_entity['size'] * 30 * self.global_scale
                other_rect = pygame.Rect(other_x - other_size, other_y - other_size, 
                                       other_size * 2, other_size * 2)
                
                if tooltip_rect.colliderect(other_rect):
                    overlap_count += 1
            
            if overlap_count < min_overlap:
                min_overlap = overlap_count
                best_candidate = (candidate_x, candidate_y, triangle_side)
        
        # 如果没有找到无重叠位置，使用右侧默认位置
        if best_candidate is None:
            tooltip_x = min(x + base_size + 30, self.width - tooltip_width - 10)
            tooltip_y = max(10, min(y - tooltip_height // 2, self.height - tooltip_height - 10))
            triangle_side = 'left'
        else:
            tooltip_x, tooltip_y, triangle_side = best_candidate
        
        # 创建高质量的提示框表面
        tooltip_surface = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        
        # 极简主义背景 - 使用更加纯净的颜色
        bg_alpha = int(240 * alpha_factor)
        bg_color = (25, 28, 35, bg_alpha)  # 深色但不失优雅
        
        # 绘制弧形圆角背景
        self.draw_rounded_rect(tooltip_surface, bg_color, 
                              (0, 0, tooltip_width, tooltip_height), corner_radius)
        
        # 极简边框 - 淡蓝色弧形加粗边框
        border_alpha = int(120 * alpha_factor)  # 增加透明度让淡蓝色更明显
        border_color = (135, 206, 235, border_alpha)  # 天蓝色边框 (Sky Blue)
        self.draw_rounded_rect_outline(tooltip_surface, border_color, 
                                     (0, 0, tooltip_width, tooltip_height), corner_radius, 2)  # 加粗到2像素
        
        # 极简风格的指向箭头 - 支持四个方向
        arrow_size = 8
        if triangle_side == 'left':
            # 提示框在几何体右侧，箭头在左边指向几何体
            arrow_points = [
                (-arrow_size, tooltip_height // 2 - arrow_size),
                (-arrow_size, tooltip_height // 2 + arrow_size),
                (-2, tooltip_height // 2)
            ]
        elif triangle_side == 'right':
            # 提示框在几何体左侧，箭头在右边指向几何体
            arrow_points = [
                (tooltip_width + arrow_size, tooltip_height // 2 - arrow_size),
                (tooltip_width + arrow_size, tooltip_height // 2 + arrow_size),
                (tooltip_width + 2, tooltip_height // 2)
            ]
        elif triangle_side == 'top':
            # 提示框在几何体下方，箭头在顶部指向几何体
            arrow_points = [
                (tooltip_width // 2 - arrow_size, -arrow_size),
                (tooltip_width // 2 + arrow_size, -arrow_size),
                (tooltip_width // 2, -2)
            ]
        elif triangle_side == 'bottom':
            # 提示框在几何体上方，箭头在底部指向几何体
            arrow_points = [
                (tooltip_width // 2 - arrow_size, tooltip_height + arrow_size),
                (tooltip_width // 2 + arrow_size, tooltip_height + arrow_size),
                (tooltip_width // 2, tooltip_height + 2)
            ]
        
        # 绘制柔和的箭头
        arrow_color = (45, 55, 70, bg_alpha)
        pygame.draw.polygon(tooltip_surface, arrow_color, arrow_points)
        
        self.screen.blit(tooltip_surface, (tooltip_x, tooltip_y))
        
        # 极简主义文字设计
        padding = 20  # 增加内边距
        line_height = 24  # 增加行高以提升可读性
        y_offset = tooltip_y + padding
        
        # 主标题 - 国家名称，使用加粗字体突出显示
        name = entity['entity']
        if len(name) > 22:
            name = name[:19] + "..."
        
        # 主标题颜色 - 纯白色，使用加粗字体
        title_alpha = int(255 * alpha_factor)
        title_color = (255, 255, 255, title_alpha)
        name_text = self.bold_font.render(name, True, title_color)  # 使用加粗字体
        text_x = tooltip_x + padding
        self.screen.blit(name_text, (text_x, y_offset))
        y_offset += line_height + 8  # 标题后额外间距
        
        # 识字率 - 主要数据，使用加粗字体突出显示
        literacy_rate = entity['literacy_rate']
        literacy_text = f"{literacy_rate:.1f}%"
        
        # 根据识字率选择颜色 - 简洁的语义化配色
        if literacy_rate >= 90:
            literacy_color = (120, 220, 120, title_alpha)  # 柔和的绿色
        elif literacy_rate >= 70:
            literacy_color = (220, 200, 120, title_alpha)  # 柔和的黄色
        else:
            literacy_color = (220, 140, 120, title_alpha)  # 柔和的橙色
        
        literacy_render = self.bold_font.render(literacy_text, True, literacy_color)  # 使用加粗字体
        self.screen.blit(literacy_render, (text_x, y_offset))
        
        # 小标签 - "Literacy Rate" 使用常规字体
        label_alpha = int(180 * alpha_factor)
        label_color = (160, 170, 180, label_alpha)
        label_text = self.small_font.render("Literacy Rate", True, label_color)
        label_x = text_x + literacy_render.get_width() + 12
        label_y = y_offset + 4  # 轻微下移对齐
        self.screen.blit(label_text, (label_x, label_y))
        y_offset += line_height
        
        # 形状信息 - 次要信息，使用小号常规字体
        shape_name = entity['shape'].title()
        shape_alpha = int(160 * alpha_factor)
        shape_color = (140, 150, 165, shape_alpha)
        shape_text = self.small_font.render(f"Shape: {shape_name}", True, shape_color)
        self.screen.blit(shape_text, (text_x, y_offset))
        
        # 更新淡出计时器
        self.data_tooltip['fade_timer'] += 1
        if self.data_tooltip['fade_timer'] >= self.data_tooltip['max_fade_time']:
            self.data_tooltip['visible'] = False
    
    def show_data_tooltip(self, entity, position):
        """显示数据对话框"""
        self.data_tooltip = {
            'visible': True,
            'entity': entity,
            'position': position,
            'fade_timer': 0,
            'max_fade_time': 180
        }
    
    def run(self):
        """运行艺术生成器"""
        if not self.load_data():
            return
        
        print("🎨 Starting Abstract Geometric Art Generator")
        print("Controls:")
        print("  ESC - Exit")
        print("  SPACE - Pause/Resume")
        print("  S - Save Screenshot")
        print("  H - Toggle Info Panel")
        print("  Click - Select Entity")
        print("  Mouse - Attract nearby entities")
        
        while self.running:
            self.handle_events()
            
            # 更新动画效果
            if not self.paused:
                self.update_click_animations()
            
            self.render_frame()
            
            # 更新时间和FPS监控
            if not self.paused:
                self.time += self.clock.tick(60)  # 60 FPS
            else:
                self.clock.tick(60)  # 保持帧率但不更新时间
            
            # 更新FPS计算
            self.fps_counter += 1
            self.fps_timer += self.clock.get_time()
            
            if self.fps_timer >= 1000:  # 每秒更新一次FPS显示
                self.current_fps = self.fps_counter * 1000 / self.fps_timer
                self.fps_counter = 0
                self.fps_timer = 0
                
                # Periodic cache cleanup to prevent memory bloat
                self.cache_frame += 1
                if self.cache_frame % 300 == 0:  # Every 5 seconds at 60fps
                    self.cleanup_caches()
    
    def cleanup_caches(self):
        """Periodic cache cleanup to prevent memory issues"""
        # Clear older cache entries periodically
        if len(self.surface_cache) > 150:
            keys_to_remove = list(self.surface_cache.keys())[:75]
            for key in keys_to_remove:
                del self.surface_cache[key]
        
        if len(self.color_cache) > 500:
            keys_to_remove = list(self.color_cache.keys())[:250]
            for key in keys_to_remove:
                del self.color_cache[key]
                
        if len(self.math_cache) > 300:
            keys_to_remove = list(self.math_cache.keys())[:150]
            for key in keys_to_remove:
                del self.math_cache[key]
                
        if len(self.blur_cache) > 100:
            keys_to_remove = list(self.blur_cache.keys())[:50]
            for key in keys_to_remove:
                del self.blur_cache[key]
        
        pygame.quit()
        print("👋 Geometric Art Generator Closed")

def main():
    """Main function"""
    engine = GeometricArtEngine(1200, 800)
    engine.run()

if __name__ == "__main__":
    main()