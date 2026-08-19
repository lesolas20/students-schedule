container-engine := require("docker")
compose-provider := require("docker")

default:
    @ just --list

# Create and start the entire stack
start:
    @ just start-fetcher

# Tear down the entire stack
stop:
    @ just stop-fetcher

# Prepare for a clean rebuild
clean:
    # Stop all services
    @- just stop-fetcher
    @- {{ container-engine }} stop students-schedule-fetcher

    # Remove all service containers
    @- {{ container-engine }} rm power-outages-tracker-schedule-fetcher

    # Remove all service images
    @- {{ container-engine }} rmi students-schedule-fetcher

# Start the fetcher service
[working-directory("service/fetcher")]
start-fetcher:
    {{ compose-provider }} compose up --detach fetcher

# Stop the fetcher service
[working-directory("service/fetcher")]
stop-fetcher:
    {{ compose-provider }} compose down
