# LoadingScreen.py

import pygame
import threading

loading_active = False
loading_thread = None

def _show_loading():
    """Create pygame loading window"""
    global loading_active
    
    pygame.init()
    screen = pygame.display.set_mode((300, 100))
    pygame.display.set_caption("Loading")
    
    font = pygame.font.SysFont('Arial', 16)
    text = font.render('Loading CPE Test Manager...', True, (255, 255, 255))
    
    clock = pygame.time.Clock()
    
    while loading_active:
        screen.fill((28, 28, 28))  # Dark background
        screen.blit(text, (20, 40))
        pygame.display.flip()
        clock.tick(30)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                loading_active = False
    
    pygame.quit()

def start_loading():
    """Start loading screen"""
    global loading_active, loading_thread
    loading_active = True
    loading_thread = threading.Thread(target=_show_loading, daemon=True)
    loading_thread.start()

def stop_loading():
    """Stop loading screen"""
    global loading_active
    loading_active = False
