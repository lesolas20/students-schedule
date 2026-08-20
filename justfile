container-engine := require("docker")
compose-provider := require("docker")
network-name := "students-schedule-internal"

default:
    @ just --list

# Create and start the entire stack
start:
    @ just create-network
    @ just start-database
    @ just start-fetcher

# Tear down the entire stack
stop:
    @ just stop-fetcher
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
    @- {{ container-engine }} stop students-schedule-database

    # Remove all service containers
    @- {{ container-engine }} rm students-schedule-fetcher
    @- {{ container-engine }} rm students-schedule-database

    # Remove all service images
    @- {{ container-engine }} rmi students-schedule-fetcher
    @- {{ container-engine }} rmi students-schedule-database

    # Miscellaneous
    @- just remove-network

# Start the fetcher service
[working-directory("service/fetcher")]
start-fetcher:
    {{ compose-provider }} compose up --detach fetcher

# Stop the fetcher service
[working-directory("service/fetcher")]
stop-fetcher:
    {{ compose-provider }} compose down

# Start the database service
[working-directory("service/database")]
start-database:
    {{ compose-provider }} compose up --detach database

# Stop the database service
[working-directory("service/database")]
stop-database:
    {{ compose-provider }} compose down
