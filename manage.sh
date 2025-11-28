#!/bin/bash

# --- НАЛАШТУВАННЯ ---
PROJECT_ID=$(gcloud config get-value project)
REGION="europe-central2"
REPO_NAME="iot-repo"
REPO_PATH="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME"

# Кольори для краси
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}--- IoT Lab Manager ($PROJECT_ID) ---${NC}"

PS3='Вибери дію: '
options=("Оновити/Запустити ВСЕ" "Оновити тільки Емулятор" "Оновити тільки Процесор" "ПАУЗА" "ВИДАЛИТИ ВСЕ" "Вихід")
select opt in "${options[@]}"
do
    case $opt in
        "Оновити/Запустити ВСЕ")
            echo -e "${GREEN}1. Збираємо образи...${NC}"
            gcloud builds submit --tag $REPO_PATH/emulator-image:latest .
            gcloud builds submit --tag $REPO_PATH/processor-image:latest processor/
            
            echo -e "${GREEN}2. Деплоїмо Емулятор...${NC}"
            gcloud run deploy iot-emulator-service \
                --image $REPO_PATH/emulator-image:latest \
                --region $REGION \
                --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
                --allow-unauthenticated \
                --min-instances=1 \
                --max-instances=1

            echo -e "${GREEN}3. Деплоїмо Процесор...${NC}"
            gcloud run deploy iot-processor-service \
                --image $REPO_PATH/processor-image:latest \
                --region $REGION \
                --allow-unauthenticated
            
            echo -e "${GREEN}ГОТОВО!${NC}"
            break
            ;;
            
        "Оновити тільки Емулятор")
            echo -e "${GREEN}Збираємо та оновлюємо Емулятор...${NC}"
            gcloud builds submit --tag $REPO_PATH/emulator-image:latest .
            gcloud run deploy iot-emulator-service \
                --image $REPO_PATH/emulator-image:latest \
                --region $REGION \
                --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
                --allow-unauthenticated \
                --min-instances=1 \
                --max-instances=1
            break
            ;;

        "Оновити тільки Процесор")
            echo -e "${GREEN}Збираємо та оновлюємо Процесор...${NC}"
            gcloud builds submit --tag $REPO_PATH/processor-image:latest processor/
            gcloud run deploy iot-processor-service \
                --image $REPO_PATH/processor-image:latest \
                --region $REGION \
                --allow-unauthenticated
            break
            ;;

        "ПАУЗА")
            echo -e "${YELLOW}Зменшуємо кількість інстансів до 0 (гроші не списуються)...${NC}"
            # Емулятор перестане працювати, бо ми прибираємо min-instances=1
            gcloud run services update iot-emulator-service --region $REGION --min-instances=0
            # Процесор теж засинає
            gcloud run services update iot-processor-service --region $REGION --min-instances=0
            echo -e "${GREEN}Сервіси 'заснули'. Щоб запустити знову - вибери пункт 1 або 2.${NC}"
            break
            ;;

        "ВИДАЛИТИ ВСЕ")
            echo -e "${RED}УВАГА! Видаляємо сервіси...${NC}"
            gcloud run services delete iot-emulator-service --region $REGION --quiet
            gcloud run services delete iot-processor-service --region $REGION --quiet
            echo -e "${GREEN}Сервіси видалено.${NC}"
            break
            ;;

        "Вихід")
            break
            ;;
        *) echo "Невірний вибір $REPLY";;
    esac
done
