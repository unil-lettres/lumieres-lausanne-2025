# Lumières Lausanne

This repository contains the code and documentation for the Lumières.Lausanne 
website, hosted by the University of Lausanne. The website is dedicated to showcasing 
the rich cultural and intellectual heritage of the Swiss Enlightenment period. 
Built with Django, the site offers a comprehensive platform for academic and research purposes.

## Installation

To set up the project locally, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/XavierBeheydt/lumieres-lausanne
   ```

2. Navigate to the project directory:
   ```bash
   cd lumieres-lausanne
   ```

3. Copy the db dump file to `backup/sqldump/v2025/2025_LL_django-v5.2.sql`.

4. Install media files to `app/media/`.

5. Reopen the project in container:
   
   <kbd>CTRL</kbd> + <kbd>SHIFT</kbd> + <kbd>P</kbd> and select `Remote-Containers: Reopen in Container`

7. To proceed to db restore:
   ```bash
   make dev/up  ## Run db and phpmyadmin services
   make migration/db/restore
   ```

8. To run the server:
   ```bash
   make dev/runserver
   ```

> For more details about make commands, please refer to the `Makefile` in the root directory and sub makefiles in the `make` directory.
