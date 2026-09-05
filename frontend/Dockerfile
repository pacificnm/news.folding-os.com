# Build the React SPA, serve with nginx (same pattern as every other app's frontend).
FROM node:24-slim AS build
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY package.json ./

# foldingos-ui is a private repo; the GitHub PAT is injected as a BuildKit
# secret, used only for this single `npm install` layer, and unset before the
# layer is committed so it never lands in the image:
#   docker build --secret id=github_token,env=GITHUB_TOKEN .
RUN --mount=type=secret,id=github_token \
    git config --global url."https://$(cat /run/secrets/github_token)@github.com/".insteadOf "https://github.com/" \
    && npm install --no-audit --no-fund \
    && git config --global --unset url."https://$(cat /run/secrets/github_token)@github.com/".insteadOf

COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
# 3006 = news's slot in site.md's port table
EXPOSE 3006
