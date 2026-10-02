import { createRequire } from "node:module";
import { resolve } from "node:path";
import babel from "@rolldown/plugin-babel";
import autoprefixer from "autoprefixer";
import { defineConfig } from "vite";

const require = createRequire(import.meta.url);

export default defineConfig(({ mode }) => ({
    root: import.meta.dirname,
    base: "./",
    publicDir: "src/assets",
    plugins: [
        {
            name: "theme-assets",
            buildStart() {
                this.addWatchFile(resolve(import.meta.dirname, "src/assets"));
            },
        },
        babel({
            presets: ["@babel/preset-env"],
            plugins: [
                [
                    "polyfill-corejs3",
                    {
                        method: "usage-global",
                        version: require("core-js/package.json").version,
                    },
                ],
            ],
        }),
    ],
    css: {
        devSourcemap: true,
        postcss: {
            plugins: [autoprefixer()],
        },
    },
    build: {
        outDir: resolve(import.meta.dirname, "static"),
        emptyOutDir: false,
        assetsInlineLimit: 0,
        cssCodeSplit: false,
        modulePreload: false,
        sourcemap: true,
        license: { fileName: "app.js.LICENSE.txt" },
        target: "es2015",
        minify: mode === "production",
        cssMinify: mode === "production",
        rolldownOptions: {
            input: resolve(import.meta.dirname, "src/app.js"),
            output: {
                format: "iife",
                codeSplitting: false,
                entryFileNames: "app.js",
                assetFileNames(asset) {
                    if (asset.names.some((name) => name.endsWith(".css"))) {
                        return "app.css";
                    }
                    return "[name][extname]";
                },
            },
        },
    },
}));
