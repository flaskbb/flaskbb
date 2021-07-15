const path = require("path");
const webpack = require("webpack");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const { CleanWebpackPlugin } = require("clean-webpack-plugin");

module.exports = {
    entry: {
        app: "./src/app",
    },
    output: {
        filename: "[name].js",
        publicPath: "/static/",
        path: path.resolve("./static/"),
        library: "[name]",
        libraryTarget: "umd",
    },
    resolve: {
        extensions: [".ts", ".tsx", ".js", ".json"],
    },
    plugins: [
        new CleanWebpackPlugin({
            cleanStaleWebpackAssets: false,
        }),
        new MiniCssExtractPlugin({
            filename: "[name].css",
            chunkFilename: "[id].css",
        }),
        new webpack.ProvidePlugin({
            $: "jquery",
            jQuery: "jquery",
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
                            "@babel/proposal-class-properties",
                            "@babel/proposal-object-rest-spread",
                        ],
                    },
                },
            },

            {
                test: /\.scss$/,
                use: [
                    { loader: MiniCssExtractPlugin.loader },
                    { loader: "css-loader" },
                    { loader: "postcss-loader" },
                    { loader: "sass-loader" },
                ],
            },
            {
                test: /\.css$/,
                use: [MiniCssExtractPlugin.loader, "css-loader"],
            },
            {
                test: /\.(ico|jpg|jpeg|png|gif|pdf|eot|otf|webp|svg|ttf|woff|woff2|xml|webmanifest)(\?.*)?$/,
                use: {
                    loader: "file-loader",
                    options: {
                        name: "[name].[ext]",
                    },
                },
            },
        ],
    },
};
