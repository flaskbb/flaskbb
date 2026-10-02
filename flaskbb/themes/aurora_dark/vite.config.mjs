import { resolve } from "node:path";
import auroraConfig from "../aurora/vite.config.mjs";

export default (environment) => {
    const config = auroraConfig(environment);
    return {
        ...config,
        root: import.meta.dirname,
        publicDir: false,
        plugins: [],
        css: {
            ...config.css,
            preprocessorOptions: {
                scss: {
                    loadPaths: [resolve(import.meta.dirname, "../aurora/node_modules")],
                },
            },
        },
        build: {
            ...config.build,
            license: false,
            outDir: resolve(import.meta.dirname, "static"),
            rolldownOptions: {
                ...config.build.rolldownOptions,
                input: resolve(import.meta.dirname, "src/scss/styles.scss"),
            },
        },
    };
};
