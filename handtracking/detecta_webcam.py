import cv2
import mediapipe as mp
import subprocess
import os
import pyautogui

# Inicializa o Mediapipe para detecção de mãos
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands()

# Configuração da câmera
camera = cv2.VideoCapture(0)
resolution_x = 1280
resolution_y = 720
camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution_x)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution_y)

# Variáveis para armazenar processos dos programas
notepad_process = None
mspaint_process = None
calc_process = None
vlc_process = None

# Caminho do VLC e do arquivo de música
vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
music_file_path = "music/test.mp3"

def find_coord_hand(img, side_inverted=False):
    """ Detecta as coordenadas da mão na imagem. """
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  
    result = hands.process(img_rgb)
    all_hands = []

    if result.multi_hand_landmarks:
        for hand_side, hand_landmark in zip(result.multi_handedness, result.multi_hand_landmarks):
            hand_info = {}  
            coords = []
            for mark in hand_landmark.landmark:
                coord_x = int(mark.x * resolution_x)
                coord_y = int(mark.y * resolution_y)
                coord_z = int(mark.z * resolution_x)
                coords.append((coord_x, coord_y, coord_z))
            hand_info["coordenadas"] = coords

        if side_inverted:
            if hand_side.classification[0].label == "Left":
                hand_info["side"] = "Right"
            else:
                hand_info["side"] = "Left" 
        else:
            hand_info["side"] = hand_side.classification[0].label  
            all_hands.append(hand_info)
            print(hand_info["side"])
            mp_drawing.draw_landmarks(img, hand_landmark, mp_hands.HAND_CONNECTIONS)  
    
    return img, all_hands 

def fingers_raised(hand):
    """ Verifica quais dedos estão levantados. """
    fingers = []
    for fingertip in [8, 12, 16, 20]:
        if hand['coordenadas'][fingertip][1] < hand['coordenadas'][fingertip-2][1]:
            fingers.append(True)
        else:
            fingers.append(False)
    return fingers       

def start_program(program):
    """ Inicia um programa. """
    return subprocess.Popen(program, shell=True)

def close_program(process_name):
    """ Fecha um programa pelo nome do processo. """
    os.system(f"TASKKILL /IM {process_name} /F")

def send_keypress(key):
    """ Simula uma tecla pressionada. """
    pyautogui.press(key)

while camera.isOpened():
    # Captura e inverte a imagem da câmera
    ret, frame = camera.read()
    frame = cv2.flip(frame, 1)  
    if not ret:
        print("Frame Vazio da Camera")
        continue
    
    # Processa a imagem para detectar as mãos
    img, all_hands = find_coord_hand(frame, False) 
    
    if len(all_hands) == 1:
        info_finger_hand = fingers_raised(all_hands[0])
        
        # Se o gesto for indicador e mindinho levantados, encerra o programa
        if info_finger_hand == [True, False, False, True]:
            break
        
        # Se os dedos indicador, médio e mindinho estiverem levantados, abre o VLC e toca música
        elif info_finger_hand == [True, True, False, True]:
            vlc_process = start_program(f'"{vlc_path}" "{music_file_path}" ')
        
        # Se apenas o indicador estiver levantado, abre o Bloco de Notas
        elif info_finger_hand == [True, False, False, False] and notepad_process is None:
            notepad_process = start_program("notepad")   
        
        # Se indicador e médio estiverem levantados, abre a Calculadora
        elif info_finger_hand == [True, True, False, False] and calc_process is None:
            calc_process = start_program("calc")
        
        # Se indicador, médio e anelar estiverem levantados, abre o Paint
        elif info_finger_hand == [True, True, True, False] and mspaint_process is None:
            mspaint_process = start_program("mspaint")
        
        # Se a mão estiver fechada, fecha os programas abertos
        elif info_finger_hand == [False, False, False, False]:
            if notepad_process is not None:
                close_program("notepad.exe")
                notepad_process = None
            if calc_process is not None:
                close_program("CalculatorApp.exe")
                calc_process = None
            if mspaint_process is not None:
                close_program("mspaint.exe")
                mspaint_process = None
            if vlc_process is not None:
                send_keypress("Space")  # Pausa a música no VLC
    
    # Exibe a imagem da câmera com as marcações das mãos
    cv2.imshow("Camera", img)  
    key = cv2.waitKey(1)
    if key == 27:  # Tecla ESC para sair
        break
