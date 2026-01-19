const path = require("path");
const webpack = require("webpack");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = {
    entry: {
        app: "./src/app.js",
    },
    output: {
        filename: "[name].js",
        publicPath: "/static/",
        path: path.resolve("./static/"),
        library: "[name]",
        libraryTarget: "umd",
        assetModuleFilename: '[name][ext]',
        devtoolModuleFilenameTemplate: 'http://[resource-path]?[loaders]',
    },
    resolve: {
        extensions: [".ts", ".tsx", ".js", ".json"],
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: "[name].css",
            chunkFilename: "[name].css",
        }),
    ],
    optimization: {
        splitChunks: {
            maxInitialRequests: Infinity,
            minSize: 0,
            cacheGroups: {
                vendor: {
                    test(mod, chunks) {
                        // exclude anything outside of node_modules
                        if (
                            mod.resource &&
                            !mod.resource.includes("node_modules")
                        ) {
                            return false;
                        }

                        // Exclude CSS - We already collect the CSS
                        if (mod.constructor.name === "CssModule") {
                            return false;
                        }

                        // return all other node modules
                        return true;
                    },
                    name: "vendors",
                    chunks: "all",
                    enforce: true,
                },
            },
        },
    },
    module: {
        rules: [
            {
                test: /\.(j|t)sx?$/,
                exclude: /node_modules/,
                use: {
                    loader: "babel-loader",
                    options: {
                        presets: [
                            [
                                "@babel/preset-env",
                                {
                                    targets: { ie: "11" },
                                    useBuiltIns: "entry",
                                    corejs: 3,
                                },
                            ],
                            "@babel/preset-typescript",
                        ],
                        plugins: [
                            "@babel/plugin-syntax-dynamic-import",
                            "@babel/plugin-transform-class-properties",
                            "@babel/plugin-transform-object-rest-spread",
                        ],
                    },
                },
            },

            {
                test: /\.scss$/,
                use: [
                    { loader: MiniCssExtractPlugin.loader },
                    {
                        loader: "css-loader",
                        options: {
                            sourceMap: true,
                        }
                    },
                    {
                        loader: "postcss-loader",
                        options: {
                            sourceMap: true,
                            postcssOptions: {
                                plugins: [
                                    [
                                        "autoprefixer"
                                    ],
                                ],
                            },
                        },
                    },
                    {
                        loader: "sass-loader",
                        options: {
                            sourceMap: true,
                        }
                    },
                ],
            },

            {
                test: /\.css$/,
                use: [MiniCssExtractPlugin.loader, "css-loader"],
            },

            {
                test: /\.(png|svg|jpg|jpeg|gif|ico)$/i,
                type: 'asset/resource',
            },

            {
                test: /\.(woff|woff2|eot|ttf|otf)$/i,
                type: 'asset/resource',
            },
        ],
    },
};
