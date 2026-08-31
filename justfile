container-engine := require("docker")
compose-provider := require("docker")
network-name := "students-schedule-internal"


set default-list := true

# Create and start the entire stack
[group("start")]
start:
    @ just create-network
    @ just start-database
    @ just start-frontend-telegram
    @ just start-fetcher

# Tear down the entire stack
[group("stop")]
stop:
    @ just stop-fetcher
    @ just stop-frontend-telegram
    @ just stop-database
    @ just remove-network

# Create the internal network
create-network:
    {{ container-engine }} network create --driver bridge --internal {{ network-name }}

# Remove the internal network
remove-network:
    {{ container-engine }} network remove --force {{ network-name }}

# Prepare for a clean rebuild
clean:
    # Stop all services
    @- just stop-fetcher
    @- just stop-database

    @- {{ container-engine }} stop students-schedule-fetcher
    @- {{ container-engine }} stop students-schedule-frontend-telegram
    @- {{ container-engine }} stop students-schedule-database

    # Remove all service containers
    @- {{ container-engine }} rm students-schedule-fetcher
    @- {{ container-engine }} rm students-schedule-frontend-telegram
    @- {{ container-engine }} rm students-schedule-database

    # Remove all service images
    @- {{ container-engine }} rmi students-schedule-fetcher
    @- {{ container-engine }} rmi students-schedule-frontend-telegram
    @- {{ container-engine }} rmi students-schedule-database

    # Miscellaneous
    @- just remove-network

# Start the fetcher service
[group("start")]
[working-directory("service/fetcher")]
start-fetcher:
    {{ compose-provider }} compose up --detach fetcher

# Stop the fetcher service
[working-directory("service/fetcher")]
[group("stop")]
stop-fetcher:
    {{ compose-provider }} compose down

# Start the database service
[group("start")]
[working-directory("service/database")]
start-database:
    {{ compose-provider }} compose up --detach database

# Stop the database service
[group("stop")]
[working-directory("service/database")]
stop-database:
    {{ compose-provider }} compose down

# Start the Telegram BFF service
[group("start")]
[working-directory("service/frontend-telegram")]
start-frontend-telegram:
    {{ compose-provider }} compose up --detach frontend-telegram

# Stop the Telegram BFF service
[group("stop")]
[working-directory("service/frontend-telegram")]
stop-frontend-telegram:
    {{ compose-provider }} compose down


# Extract messages from source files and generate a POT file
[group("i18n")]
[working-directory("service/frontend-telegram")]
locale-extract:
    mkdir locales/ --parents
    uv run pybabel extract \
      --input-dirs=src/frontend_telegram \
      --output-file=locales/messages-auto.pot \
      --add-comments=TR --omit-header

# Compile message catalogs to MO files
[group("i18n")]
[working-directory("service/frontend-telegram")]
locale-compile:
    uv run pybabel compile --directory=locales --use-fuzzy
    # `--use-fuzzy` is required to compile catalogs without headers until this issue is resolved: https://github.com/python-babel/babel/issues/688

# Update existing (or create) message catalogs from a POT file
[group("i18n")]
[working-directory("service/frontend-telegram")]
locale-update:
    xgettext \
      locales/messages-auto.pot locales/messages-manual.pot \
      --output=locales/messages.pot \
      --omit-header

    uv run pybabel update \
      --input-file=locales/messages.pot \
      --output-dir=locales \
      --init-missing --omit-header \
      --locale=en

    uv run pybabel update \
      --input-file=locales/messages.pot \
      --output-dir=locales \
      --init-missing --omit-header \
      --locale=uk
