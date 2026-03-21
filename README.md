# MultiCam-Analytics

## Установка
Для установки необходимо выполнить следующие команды:
```
git clone https://github.com/Stribunchick/MultiCam-Analytics.git
```
```
cd MultiCam-Analytics
```

Для корректной работы с GPU необходимо установить PyTorch с поддержкой CUDA (например, torch с версией cu121 для CUDA 12.1 и выше)
Проверить текущую версию CUDA устройства можно следующей командой
```
nvidia-smi
```
## Установка torch
```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```
## Установка зависимостей
```
pip install -r requirements.txt
```
## Запуск приложения
```
python app.py
```
