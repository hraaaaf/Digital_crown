module.exports = {
  apps: [
    {
      name: "digitalcrown-backend",
      script: "uvicorn",
      args: "backend.main:app --host 0.0.0.0 --port 8000 --workers 4",
      interpreter: "python", // S'assure d'utiliser l'environnement virtuel si PM2 est lancé depuis venv
      cwd: "./",
      watch: false, // PAS de reload en production
      env_production: {
        ENVIRONMENT: "production"
      }
    },
    {
      name: "digitalcrown-frontend",
      script: "npm",
      args: "run preview -- --host 0.0.0.0 --port 5173",
      cwd: "./",
      watch: false,
      env_production: {
        NODE_ENV: "production"
      }
    }
  ]
};
