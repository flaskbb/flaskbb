var gulp = require('gulp'),
    bower = require('gulp-bower')
    sass = require('gulp-ruby-sass'),
    minifycss = require('gulp-minify-css'),
    uglify = require('gulp-uglify'),
    rename = require('gulp-rename'),
    concat = require('gulp-concat'),
    notify = require('gulp-notify');

var config = {
     sassPath: './src',
    sassDestPath: './static/css',
    jsPath: './static/js',
     bowerDir: './bower_components' 
}

// install dependencies
gulp.task('bower', function() { 
    return bower()
         .pipe(gulp.dest(config.bowerDir)) 
});

// update dependencies
gulp.task('update', function() {
  return bower({ cmd: 'update'});
});

gulp.task('icons', function() { 
    return gulp.src(config.bowerDir + '/font-awesome/fonts/**.*') 
        .pipe(gulp.dest('./static/fonts')); 
});

gulp.task('sass', function () {
    return sass(config.sassPath + '/styles.scss', {
            style: 'compressed',
            loadPath: [
                './src/',
                 config.bowerDir + '/bootstrap-sass/assets/stylesheets',
                 config.bowerDir + '/font-awesome/scss'
            ]
        })
        .on("error", notify.onError(function (error) {
                 return "Error: " + error.message;
          }))

        // add the bootstrap-markdown style to the styles.css
        .pipe(gulp.dest(config.sassDestPath));
});

gulp.task('css', ['sass'], function() {
    return gulp.src([
            config.sassDestPath + '/styles.css',
            config.bowerDir + '/bootstrap-markdown/css/bootstrap-markdown.min.css'])
        .pipe(concat('styles.css'))
        .pipe(gulp.dest(config.sassDestPath));
})

gulp.task('scripts', function() {
    return gulp.src([config.bowerDir + '/jquery/dist/jquery.min.js',
                     config.bowerDir + '/bootstrap-sass/assets/javascripts/bootstrap.min.js',
                     config.jsPath + '/flaskbb.js'])
        .pipe(concat('scripts.min.js'))
        .pipe(uglify())
        .pipe(gulp.dest(config.jsPath));
});

// all the scripts that are needed for our texteditor
// we bundle them extra because we do not always need them
gulp.task('editor-scripts', function() {
    return gulp.src([
                     config.bowerDir + '/marked/lib/marked.js',
                     config.bowerDir + '/bootstrap-markdown/js/bootstrap-markdown.js',
                     config.bowerDir + '/jquery-textcomplete/dist/jquery.textcomplete.min.js',
                     config.jsPath + '/emoji.js',
                     config.jsPath + '/editor.js'])
        .pipe(concat('editor.min.js'))
        .pipe(uglify())
        .pipe(gulp.dest(config.jsPath));
})

// Rerun the task when a file changes
 gulp.task('watch', function() {
     gulp.watch(config.sassPath + '/*.scss', ['css']); 
});

  gulp.task('default', ['bower', 'icons', 'css', 'scripts', 'editor-scripts']);
