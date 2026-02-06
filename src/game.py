import os
import sys

import pygame
import pytmx
import pyscroll

from player import Player

# Chemin de base du projet (dossier parent de src/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_DIR = os.path.join(BASE_DIR, 'map')


class Portal:
    """Représente une zone de transition vers une autre carte."""

    def __init__(self, name, rect, target_map, target_spawn):
        self.name = name
        self.rect = rect
        self.target_map = target_map      # ex: "house.tmx"
        self.target_spawn = target_spawn  # ex: "spawn_from_lobby"


class Map:
    """Gère les données d'une carte chargée."""

    def __init__(self, name, walls, portals):
        self.name = name
        self.walls = walls
        self.portals = portals


class Game:

    def __init__(self):
        """
        Initialise la fenêtre du jeu, charge la carte principale,
        initialise le joueur et configure les collisions.
        """
        # Créer la fenêtre du jeu
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Paimon - Adventure")

        # Carte actuelle et groupe pyscroll
        self.current_map = None
        self.group = None

        # Cooldown de teleportation (empeche la boucle infinie entre portails)
        self.portal_cooldown = 0

        # Générer un joueur (position temporaire, mise à jour au chargement de la carte)
        self.player = Player(0, 0)

        # Charger la carte initiale
        self.load_map('carte.tmx', 'player')

    def _get_object_by_name(self, tmx_data, name):
        """Cherche un objet par son nom dans les données TMX."""
        for obj in tmx_data.objects:
            if obj.name == name:
                return obj
        return None

    def load_map(self, map_name, spawn_point_name):
        """
        Charge une carte et positionne le joueur au point de spawn spécifié.

        Args:
            map_name: Nom du fichier TMX (ex: 'carte.tmx', 'house.tmx')
            spawn_point_name: Nom de l'objet point de spawn dans le TMX
        """
        # Charger les données TMX
        tmx_path = os.path.join(MAP_DIR, map_name)
        tmx_data = pytmx.util_pygame.load_pygame(tmx_path)

        # Créer le renderer pyscroll
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 2

        # Collecter les murs (collisions)
        walls = []
        for obj in tmx_data.objects:
            if obj.type == "collision":
                walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

        # Collecter les portails
        portals = []
        for obj in tmx_data.objects:
            if obj.type == "portal":
                # Récupérer les propriétés personnalisées du portail
                target_map = obj.properties.get('target_map', '')
                target_spawn = obj.properties.get('target_spawn', 'default')

                portal = Portal(
                    name=obj.name,
                    rect=pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                    target_map=target_map,
                    target_spawn=target_spawn
                )
                portals.append(portal)

        # Créer l'objet Map
        self.current_map = Map(map_name, walls, portals)

        # Recréer le groupe pyscroll
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=5)
        self.group.add(self.player)

        # Positionner le joueur au point de spawn
        spawn_point = self._get_object_by_name(tmx_data, spawn_point_name)
        if spawn_point:
            self.player.position[0] = spawn_point.x
            self.player.position[1] = spawn_point.y
        else:
            print(f"Attention: spawn '{spawn_point_name}' non trouvé dans {map_name}, position par défaut (100, 100)")
            self.player.position[0] = 100
            self.player.position[1] = 100

        self.player.update()
        self.player.save_location()

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

    def check_portals(self):
        """Vérifie si le joueur entre dans un portail et effectue la transition."""
        if self.portal_cooldown > 0:
            self.portal_cooldown -= 1
            return

        for portal in self.current_map.portals:
            if self.player.feet.colliderect(portal.rect):
                self.load_map(portal.target_map, portal.target_spawn)
                self.portal_cooldown = 30  # ~0.5 seconde a 60 FPS
                return  # Sortir après le changement de carte

    def update(self):
        """
        Met à jour l'état du jeu, y compris les collisions et les changements de carte.
        """
        self.group.update()

        # Vérifier les portails
        self.check_portals()

        # Vérification de la collision avec les murs
        for sprite in self.group.sprites():
            if hasattr(sprite, 'feet') and sprite.feet.collidelist(self.current_map.walls) > -1:
                sprite.move_back()

    
    def run(self):
        """
        Boucle principale du jeu.
        """
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.player.save_location()  # Mémorise la location du joueur
            self.handle_input()
            self.update()
            self.group.center(self.player.rect.center)  # Permet de centrer la caméra sur le "player"
            self.group.draw(self.screen)
            pygame.display.flip()

            clock.tick(60)  # Définit les FPS

        pygame.quit()