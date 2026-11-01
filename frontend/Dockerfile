FROM node:24-alpine

WORKDIR /app

# Enable Corepack and activate the project's pnpm version.
RUN corepack enable \
    && corepack prepare pnpm@12.11.2 --activate

# Install dependencies using the lockfile.
COPY frontend/package.json frontend/pnpm-lock.yaml ./

RUN pnpm install --frozen-lockfile

# Copy the frontend source code.
COPY frontend/ ./

EXPOSE 5173

# Start Vite and expose it outside the container.
CMD ["pnpm", "dev", "--host", "0.0.0.0"]
