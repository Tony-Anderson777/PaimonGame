import os
import pygame
import pytmx
import pyscroll
from pygame.math import Vector2  # Importe Vector2 pour les positions par défaut

from player import Player

# Chemin de base du projet (dossier parent de src/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_DIR = os.path.join(BASE_DIR, 'map')


def get_object_by_name(tmx_data, name):
    """Cherche un objet par son nom dans les données TMX."""
    for obj in tmx_data.objects:
        if obj.name == name:
            return obj
    return None


class Game:

    def __init__(self):
        """
        Initialise la fenêtre du jeu, charge la carte principale,
        initialise le joueur et configure les collisions.
        """
        # Créer la fenêtre du jeu
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Paimon - Adventure")

        # Charger la carte (tmx)
        tmx_data = pytmx.util_pygame.load_pygame(os.path.join(MAP_DIR, 'carte.tmx'))
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 2

        # Générer un joueur
        player_position = get_object_by_name(tmx_data,"player")
        # Vérifier si l'objet 'player' existe dans la carte TMX
        if player_position is None:
            print(
                "Attention : L'objet de départ du joueur 'player' n'a pas été trouvé dans carte.tmx. Utilisation de la position par défaut (100, 100).")
            # Définir une position par défaut si l'objet n'est pas trouvé
            player_position = Vector2(100, 100)

        self.player = Player(player_position.x, player_position.y)

        # Définir une liste qui va stocker les rectangles de collision
        self.walls = []
        for obj in tmx_data.objects:
            if obj.type == "collision":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

        # Dessiner le groupe de calques (map et joueur)
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=5)
        self.group.add(self.player)

        # Définir le rectangle de collision pour entrer dans la maison
        enter_house = get_object_by_name(tmx_data,'enter_house')
        if enter_house is not None:
            self.enter_house_rect = pygame.Rect(enter_house.x, enter_house.y, enter_house.width, enter_house.height)
        else:
            print("Attention : L'objet 'enter_house' n'a pas été trouvé dans carte.tmx. Le rectangle de collision ne sera pas défini.")
            self.enter_house_rect = pygame.Rect(0, 0, 0, 0)

        # Initialiser l'état de la carte actuelle
        self.map = 'world'

    def handle_input(self):
        """
        Gère les entrées du clavier pour le mouvement du joueur.
        """
        pressed = pygame.key.get_pressed()

        # Mouvement et changement d'animation du joueur
        if pressed[pygame.K_UP]:
            self.player.move_up()
            self.player.change_animation('up')
        elif pressed[pygame.K_DOWN]:
            self.player.move_down()
            self.player.change_animation('down')
        elif pressed[pygame.K_LEFT]:
            self.player.move_left()
            self.player.change_animation('left')
        elif pressed[pygame.K_RIGHT]:
            self.player.move_right()
            self.player.change_animation('right')

    def switch_house(self):
        """
        Change la carte vers l'intérieur de la maison.
        """
        # Charger la carte de la maison (house.tmx)
        tmx_data = pytmx.util_pygame.load_pygame(os.path.join(MAP_DIR, 'house.tmx'))
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 2

        # Redéfinir les murs pour la carte de la maison
        self.walls = []
        for obj in tmx_data.objects:
            if obj.type == "collision":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

        # Redéfinir le groupe de calques avec la nouvelle carte
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=5)
        self.group.add(self.player)

        # Définir le rectangle de collision pour sortir de la maison (exit_house)
        enter_house = get_object_by_name(tmx_data,'exit_house')
        if enter_house is not None:
            self.enter_house_rect = pygame.Rect(enter_house.x, enter_house.y, enter_house.width, enter_house.height)
        else:
            print("Attention : L'objet 'exit_house' n'a pas été trouvé dans house.tmx. Le rectangle de collision ne sera pas défini.")
            self.enter_house_rect = pygame.Rect(0, 0, 0, 0)

        # Récupérer le point de spawn à l'intérieur de la maison
        spawn_house_point = get_object_by_name(tmx_data, 'spawn_house')
        if spawn_house_point is not None:
            self.player.position[0] = spawn_house_point.x
            self.player.position[1] = spawn_house_point.y - 20
            self.player.update()
            self.player.save_location()  # Évite que move_back() renvoie à l'ancienne carte

    def switch_world(self):
        """
        Change la carte vers le monde extérieur.
        """
        # Charger la carte du monde (carte.tmx)
        tmx_data = pytmx.util_pygame.load_pygame(os.path.join(MAP_DIR, 'carte.tmx'))
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 2

        # Redéfinir les murs pour la carte du monde
        self.walls = []
        for obj in tmx_data.objects:
            if obj.type == "collision":
                self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

        # Redéfinir le groupe de calques avec la nouvelle carte
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=5)
        self.group.add(self.player)

        # Redéfinir le rectangle de collision pour entrer dans la maison (enter_house)
        enter_house = get_object_by_name(tmx_data,'enter_house')
        if enter_house is not None:
            self.enter_house_rect = pygame.Rect(enter_house.x, enter_house.y, enter_house.width, enter_house.height)
        else:
            print("Attention : L'objet 'enter_house' n'a pas été trouvé dans carte.tmx lors du retour au monde. Le rectangle de collision ne sera pas défini.")
            self.enter_house_rect = pygame.Rect(0, 0, 0, 0)

        # Récupérer le point de spawn dans le monde (point de sortie de la maison)
        spawn_world_point = get_object_by_name(tmx_data, 'enter_house_exit')
        if spawn_world_point is not None:
            self.player.position[0] = spawn_world_point.x
            self.player.position[1] = spawn_world_point.y
            self.player.update()
            self.player.save_location()  # Évite que move_back() renvoie à l'ancienne carte

    def update(self):
        """
        Met à jour l'état du jeu, y compris les collisions et les changements de carte.
        """
        self.group.update()

        # Vérifier l'entrée dans la maison
        if self.map == 'world' and self.player.feet.colliderect(self.enter_house_rect):
            self.switch_house()
            self.map = 'house'

        # Vérifier la sortie de la maison (utiliser elif pour éviter des conflits si les rectangles se chevauchent)
        elif self.map == 'house' and self.player.feet.colliderect(self.enter_house_rect):
            self.switch_world()
            self.map = 'world'

        # Vérification de la collision avec les murs
        for sprite in self.group.sprites():
            if sprite.feet.collidelist(self.walls) > -1:
                sprite.move_back()

    
    def run(self):
        """
        Boucle principale du jeu.
        """
        clock = pygame.time.Clock()
        running = True

        while running:
            self.player.save_location()  # Mémorise la location du joueur
            self.handle_input()
            self.update()
            self.group.center(self.player.rect.center)  # Permet de centrer la caméra sur le "player"
            self.group.draw(self.screen)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    

            clock.tick(60)  # Définit les FPS

        pygame.quit()
        import sys
        sys.exit()