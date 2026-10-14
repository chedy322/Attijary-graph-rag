<!-- RUN THIS FOR CELERY -->
celery -A celery_worker.celery_app worker --loglevel=info --pool=threads

<!-- DOCKER -->
docker compose up -d

<!-- INFRASTRUCTURE -->
terraform apply -auto-approve

Project 
Frontend: deployed using render
Backend: deployed in azure using VM 






