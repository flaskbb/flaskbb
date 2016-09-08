# INSTALLATION

Make sure that you have npm (nodejs) installed. You can get it from [
here](https://nodejs.org).

This theme uses SASS (https://sass-lang.com/), a CSS preprocessor, for better development.

Before you can compile the source, you need to get a few dependencies first.
This can be achieved by running ``npm install`` in the directory where **this** README is located.


# TASKS

To minimize the dependencies to build and minify our source files, we just use
npm for it.

    Usage
      npm run [TASK]

    Available tasks
      clean
        rm -f node_modules
      autoprefixer
        postcss -u autoprefixer -r static/css/*
      scss
        ./tools/build_css
      uglify
        ./tools/build_js
      imagemin
        imagemin src/img/* -o static/img
      fonts
        ./tools/build_fonts
      build:css
        npm run scss && npm run autoprefixer
      build:js
        npm run uglify
      build:images
        npm run imagemin && npm run fonts
      build:all
        npm run build:css && npm run build:js && npm run build:images
      watch:css
        onchange 'src/scss' -- npm run build:css
      watch:js
        onchange 'src/js' -- npm run build:js
      watch:all
        npm-run-all -p watch:css watch:js

To watch for changes in our JS and SCSS files, you just have to run:

``npm run watch:all``

and upon changes it will automatically rebuild the files.


# CREATING YOUR OWN THEME

See the [theming documentation](https://flaskbb.readthedocs.io/en/latest/theming.html).
