var gulp = require('gulp-help')(require('gulp')),
    bower = require('gulp-bower')
    sass = require('gulp-sass'),
    uglify = require('gulp-uglify'),
    rename = require('gulp-rename'),
    concat = require('gulp-concat'),
    notify = require('gulp-notify'),
    autoprefixer = require('gulp-autoprefixer'),
    imagemin = require('gulp-imagemin');

var basicConfig = {
    srcDir: './src',
    destDir: './static',
    bowerDir: './bower_components'
};

var config = {
    scss: {
        src: basicConfig.srcDir + '/scss',
        dest: basicConfig.destDir + '/css'
    },

    imgs: {
        src: basicConfig.srcDir + '/imgs',
        dest: basicConfig.destDir + '/imgs'
    },

    js: {
        flaskbb: basicConfig.destDir + '/js/flaskbb.js',
        emoji: basicConfig.destDir + '/js/emoji.js',
        editorConfig: basicConfig.destDir + '/js/editor.js',
        dest: basicConfig.destDir + '/js'
    },

    editor: {
        lib: basicConfig.bowerDir + '/bootstrap-markdown/js/bootstrap-markdown.js',
        parser: basicConfig.bowerDir + '/marked/lib/marked.js',
        textcomplete: basicConfig.bowerDir + '/jquery-textcomplete/dist/jquery.textcomplete.min.js'
    },

    jquery: basicConfig.bowerDir + '/jquery/dist/jquery.min.js',

    bootstrap: {
        js: basicConfig.bowerDir + '/bootstrap-sass/assets/javascripts/bootstrap.min.js',
        scss: basicConfig.bowerDir + '/bootstrap-sass/assets/stylesheets'
    },

    font: {
        icons: basicConfig.bowerDir + '/font-awesome/fonts/*.**',
        scss: basicConfig.bowerDir + '/font-awesome/scss',
        dest: basicConfig.destDir + '/fonts'
    }
};


gulp.task('bower', 'runs bower', function() {
    return bower()
        .pipe(gulp.dest(basicConfig.bowerDir))
});


gulp.task('update', 'updates the bower dependencies', function() {
    return bower({ cmd: 'update' });
});


gulp.task('icons', 'copies the icons to destDir', function() {
    return gulp.src(config.font.icons)
        .pipe(gulp.dest(config.font.dest));
});


gulp.task('image', 'optimizes the images', function() {
    return gulp.src(config.imgs.src + '/*')
        .pipe(imagemin({
            progressive: true,
            svgoPlugins: [
                { removeViewBox: false },
                { cleanupIDs: false }
            ]
        }))
        .pipe(gulp.dest(config.imgs.dest));
});


gulp.task('sass', 'compiles all scss files to one css file', function () {
    return gulp.src(config.scss.src + '/**/*.scss')
        .pipe(sass({
            outputStyle: 'compressed',
            precision: 8,
            includePaths: [
                basicConfig.srcDir + '/scss',
                config.bootstrap.scss,
                config.font.scss
            ]})
            .on('error', notify.onError(function(error) {
                return "Error: " + error.message;
            })))
        .pipe(autoprefixer('last 2 version'))
        .pipe(rename({basename: 'styles', extname: '.min.css'}))
        .pipe(gulp.dest(config.scss.dest));
});


gulp.task('main-scripts', 'concates all main js files to one js file', function() {
    return gulp.src([config.jquery,
                     config.bootstrap.js,
                     config.js.flaskbb])
        .pipe(concat('scripts.min.js'))
        .pipe(uglify())
        .pipe(gulp.dest(config.js.dest));
});


gulp.task('editor-scripts', 'concates all editor related scripts to one file', function() {
    return gulp.src([config.editor.parser,
                     config.editor.lib,
                     config.editor.textcomplete,
                     config.js.emoji,
                     config.js.editorConfig])
        .pipe(concat('editor.min.js'))
        .pipe(uglify())
        .pipe(gulp.dest(config.js.dest));
});


gulp.task('vendor-scripts', 'concates all vendor js files to one js file (useful for debugging)', function() {
    return gulp.src([config.jquery,
                     config.bootstrap.js,
                     config.editor.parser,
                     config.editor.lib,
                     config.editor.textcomplete])
        .pipe(concat('scripts.min.js'))
        .pipe(uglify())
        .pipe(gulp.dest(config.js.dest));
});


gulp.task('scripts', ['main-scripts', 'editor-scripts'], function() {});


gulp.task('watch', 'watches for .scss and .js changes', function() {
    gulp.watch(config.sassPath + '/*.scss', ['sass']);
    gulp.watch(config.jsPath + '/*.js', ['scripts'])
});

gulp.task('default', 'default command', ['bower', 'icons', 'sass', 'scripts', 'image']);
