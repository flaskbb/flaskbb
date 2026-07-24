const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

// Aurora Dark reuses the default Aurora theme's installed dependencies
const auroraModules = path.resolve(__dirname, "../aurora/node_modules");

module.exports = {
    entry: {
        app: "./src/styles.js",
    },
    output: {
        filename: "[name].js",
        publicPath: "/static/",
        path: path.resolve("./static/"),
        assetModuleFilename: "[name][ext]",
    },
    resolve: {
        extensions: [".js", ".json"],
        modules: [auroraModules, "node_modules"],
    },
    resolveLoader: {
        modules: [auroraModules, "node_modules"],
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: "[name].css",
            chunkFilename: "[name].css",
        }),
    ],
    module: {
        rules: [
            {
                test: /\.scss$/,
                use: [
                    { loader: MiniCssExtractPlugin.loader },
                    {
                        loader: "css-loader",
                        options: {
                            sourceMap: true,
                            // Fonts are reused from the default theme at
                            // /static; leave those (and any other) url()
                            // references untouched instead of bundling them.
                            url: false,
                        },
                    },
                    {
                        loader: "postcss-loader",
                        options: {
                            sourceMap: true,
                            postcssOptions: {
                                plugins: [["autoprefixer"]],
                            },
                        },
                    },
                    {
                        loader: "sass-loader",
                        options: { sourceMap: true },
                    },
                ],
            },
            {
                test: /\.css$/,
                use: [MiniCssExtractPlugin.loader, "css-loader"],
            },
            {
                test: /\.(png|svg|jpg|jpeg|gif|ico)$/i,
                type: "asset/resource",
            },
            {
                test: /\.(woff|woff2|eot|ttf|otf)$/i,
                type: "asset/resource",
            },
        ],
    },
};
