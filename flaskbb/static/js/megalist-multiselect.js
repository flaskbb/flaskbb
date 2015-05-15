!function($){
  'use strict';

 /* LIST CLASS DEFINITION
  * ========================= */

  var Megalist = function(element, $parent) {
    var html;

    if ($parent === undefined){
    //if there's no $parent then we are creating one
        this.$el = element;
        this.setOptions(this.$el.options);
        // build HTML
        html = this.buildParentDOM();
        //source list - data to choose from
        this.$el.sourceList = new Megalist(html.srcElement, this.$el);
        //destination list - data chosen by user
        this.$el.destinationList = new Megalist(html.dstElement, this.$el);

    } else {
    //else just init one of the megalistSide children
        this.init(element, $parent);
    }
    return this;
  };

  Megalist.prototype = {

    constructor: Megalist,

    /**
     * megalistSide constructor - initializes one side of megalist
     *
     * @param {object} element - jQuery object on witch megalist is initialized
     * @param {object} $parent - optional jQuery object with parent for
     *                           megalistSide initialization only
     * @return {object} - returns self
     */
    init: function(element, $parent) {
        this.$el = element;
        this.$parent = $parent;

        //defaults
        this.processedItems = {};
        this.totalItems = [];
        this.itemHeight = -1;
        this.listItems = $();
        this.suffix = undefined;
        this.yPosition = 0;
        this.filteredData = [];
        this.pageHeight = 0;
        this.scrollingActive = false;

        //init widget
        this.setOptions(this.$parent.options);
        this.getSuffix();
        this.buildDOM();
        this.bindEvents();
        this.bindData();
        this.updateLayout();
        this.generatePOST(this.conf.BUILD_FULL_POST);

        return this;
    },

    /**
     * Sets default options and extends them if configuration was provided on
     * megalist initialization
     *
     * @param {object} options - object containing options for megalist
     */
    setOptions: function(options){
        var conf = {};

        // mimimum scrollbar height in pixels
        conf.SCROLLBAR_MIN_SIZE = 12;
        // inertial delay for megalist ui update after resize event occurs
        conf.RESIZE_TIMEOUT_DELAY = 100;
        // minimum characters to trigger quicksearch filtering
        conf.MINIMUM_SEARCH_QUERY_SIZE = 3;
        // build full or simple (comma separated ids) post
        conf.BUILD_FULL_POST = false;
        // move action event name to trigger
        conf.MOVE_ACTION_NAME = 'move';
        //functional suffixes for multiselect: destination list suffix
        conf.DESTINATION_SUFFIX = 'dst';
        // functional suffixes for multiselect: source list suffix
        conf.SOURCE_SUFFIX = 'src';
        // text to display as search input placeholder
        conf.PLACEHOLDER_TEXT = 'Search';
        // time to wait for first continous scrolling
        conf.CONTINOUS_SCROLLING_FIRST_INTERVAL = 500;
        // time to wait for every next continous scrolling
        conf.CONTINOUS_SCROLLING_INTERVAL = 60;

        if (typeof options === 'object'){
            conf = $.extend(conf, options);
        }
        this.conf = conf;
    },

    /**
     * Builds required html elements for both source and destination
     * megalistSide and append them to parent element
     */
    buildParentDOM: function() {
        var srcElement, dstElement;

        this.$el.html('');
        this.$el.addClass('megalist-mutliselect');

        //create 2 containers for megalists and buttons between then append
        srcElement = $( '<div/>', {
            'id': this.$el.attr('id') + '_' + this.conf.SOURCE_SUFFIX,
            'class': 'megalist-inner'
        });
        dstElement = $( '<div/>', {
            'id': this.$el.attr('id') + '_' + this.conf.DESTINATION_SUFFIX,
            'class': 'megalist-inner'
        });
        this.$el.$moveButtons = $( '<div/>', {
            'class': 'move-buttons'
        });

        this.$el.append(srcElement, this.$el.$moveButtons, dstElement);

        return {srcElement:srcElement, dstElement:dstElement};
    },

    /**
     * Builds required html elements for megalistSide:
     * searchbox, scrollbar, move button and hidden result input
     */
    buildDOM: function() {
        var arrowIcon = 'arrow-left';

        if (this.suffix === this.conf.SOURCE_SUFFIX) {
            arrowIcon = 'arrow-right';
        }

        this.$el.wrap('<div class="megalist"></div>"');

        this.$search = $('<input/>', {
            'id': this.$el.attr('id') + '_search',
            'placeholder': this.conf.PLACEHOLDER_TEXT,
            'type': 'text'
        });
        this.$scrollbar = $('<div/>', {
            'id': this.$el.attr('id') + '_scrollbar',
            'class': 'scrollbar'
        });
        this.$scrollbarBackground = $('<div/>', {
            'class': 'scrollbar-background'
        });
        this.$moveall = $('<div/>', {
            'class': 'move-button ' + arrowIcon
        });

        if (Modernizr.svg) {
            this.$moveall.append($(
                '<svg width="32" height="32" viewBox="0 0 64 64">' +
                '<use xlink:href="#' + arrowIcon + '"></svg>'
            ));
        } else {
            this.$moveall.addClass('no-svg');
            this.$moveall.append($('<div class="svg" />'));
        }

        //attach to container in parent
        this.$parent.$moveButtons.append(this.$moveall);

        this.$input = $('<input/>', {
            'name': this.name,
            'type': 'hidden'
        });
        this.$ul = $('<ul />');

        this.$el.before(this.$search);

        // Set tabindex, so the element can be in focus
        this.$el.attr('tabindex', '-1');
    },

    /**
     * Resolves suffix for megalistSide so that it know if it's source or
     * destination side. Resolving is based on id of the container
     */
    getSuffix: function() {
        var id_tokens, lastToken;

        id_tokens = this.$el.attr('id').split('_');
        lastToken = id_tokens[id_tokens.length - 1];
        this.name = id_tokens.splice(id_tokens, id_tokens.length-1).join('_');

        if (lastToken === this.conf.SOURCE_SUFFIX) {
            this.suffix = this.conf.SOURCE_SUFFIX;
        } else if (lastToken === this.conf.DESTINATION_SUFFIX) {
            this.suffix = this.conf.DESTINATION_SUFFIX;
        }
    },

    /**
     * Returns targetList for current megalistSide. In not defined, gets proper
     * one from $parent first and stores it for later use
     *
     * @return {object} - returns target list
     */
    getTargetList: function() {
        if (!(this.targetList instanceof Object)){
            if ( this.suffix === this.conf.SOURCE_SUFFIX) {
                this.targetList = this.$parent.destinationList;
            } else if ( this.suffix === this.conf.DESTINATION_SUFFIX) {
                this.targetList = this.$parent.sourceList;
            }
        }
        return this.targetList;
    },

    /**
     * Binds all events need by the widget
     */
    bindEvents: function() {
        var self = this,
            filterEvent;

       $(window).resize(function(event){
            return self.onResize(event);
        });

        $(window).bind('keydown', function(event) {
            return self.onKeydown(event);
        });

        this.$el.mousedown(function() {
            setTimeout(function(){
                this.focus();
            }, 1);
        });

        this.$el.bind('mousewheel DOMMouseScroll', function(event) {
            event.preventDefault();
            return self.onMouseWheel(event);
        });

        this.$el.click(function(event) {
            self.processListClick(event);
        });

        this.$scrollbar.bind('mousedown', function(event) {
             self.onScrollbarStart(event);
        });

        this.$scrollbarBackground.mousedown(function(event) {
            self.scrollingActive = true;
            self.scrollDir = undefined;
            self.onScrollbarBackgroundClick(event);
        });

        this.$scrollbarBackground.mouseleave(function(event) {
            self.scrollingActive = false;
        });

        this.$scrollbarBackground.mouseup(function(event) {
            self.scrollingActive = false;
        });

        this.$moveall.click(function(event) {
            self.onMoveAll(event);
        });

        if (Modernizr.hasEvent('input', this.$search)) {
            filterEvent = 'input';
        } else {
            filterEvent = 'keyup';
        }

        this.$search.on(filterEvent, function() {
            self.yPosition = 0;
            self.filterList();
        });
    },

    /**
     * Extracts the supplied data for megalistSide from data-provider-src or
     * data-provider-dst attributes depending which side is being loaded.
     * The attributes must be set on megalist container.
     */
    bindData: function() {
        this.origData = this.$parent.attr('data-provider-' + this.suffix);
        if (this.origData.length){
            this.dataProviderOrig =  this.parseData(this.origData);
            this.$parent.attr('data-provider-' + this.suffix, '');
        } else {
            this.dataProviderOrig = {};
        }

        this.dataProvider = this.dataProviderOrig;

        this.clearSelectedIndex();

        this.$ul.find('li').each(function() {
            $(this).remove();
        });

        this.yPosition = 0;
    },

    /**
     * Parses the data extracted from container attribues. Currently two
     * formats are supported: JSON and passing old <select> element that
     * is being replaced by this widget
     *
     * @param {string} origData - string extracted from attribute
     *                            (JSON or old select html)
     * @return {Array} parsed - parsed data array
     */
    parseData: function(origData){
        var parsed = [], item = {};
        var selected = ':not(:selected)';

        //first see if it's JSON
        try {
          parsed = $.parseJSON(origData);
        } catch(e) {
          //not JSON
        }
        //ok, maybe it's being fed <option>s from an old select?
        if (origData.substr(0, 7) == '<select'){
          if (this.suffix === this.conf.DESTINATION_SUFFIX) {
              selected = ':selected';
          }
           $.map($('option', origData).filter(selected), function(opt){
               item.listValue = opt.value;
               item.label = opt.text;
               parsed.push(item);
               item = {};
           });
        } else if ((origData.indexOf('<select') > -1)){
            console.log('ERROR: the supplied string MUST start with <select');
        }

        return parsed;
    },

    /**
     * Updates responsive mutliselect on window resize by recalculating new
     * sizing and redrawing megalistSide widgets. Updating has some inertia
     * added resizing only after RESIZE_TIMEOUT_DELAY is reached
     */
    onResize: function() {
        clearTimeout(this.reizeTimeout);
        var self = this,
            totalHeight = this.dataProvider.length * this.itemHeight,
            maxPosition = totalHeight - this.$el.height();

        maxPosition = Math.max(0, maxPosition);
        this.yPosition = Math.min(this.yPosition, maxPosition);
        this.reizeTimeout = setTimeout(function() {
            self.updateLayout();
        }, this.conf.RESIZE_TIMEOUT_DELAY);
    },

    /**
    * @TODO - @FIXME
    * @param {event} event - user key press event
    */
    onKeydown: function (event) {
        var delta = 0,
            action = this.conf.MOVE_ACTION_NAME,
            self = this,
            oldindex = this.getSelectedIndex(),
            index = oldindex + delta;

        if (!this.$el.is(':focus')) {
            return;
        }

        switch (event.which) {
            case 33:  // Page up
                delta = -1 * Math.floor(this.$el.height() / this.itemHeight);
                break;

            case 34:  // Page down
                delta = Math.floor(this.$el.height() / this.itemHeight);
                break;

            case 38:  // Up
                delta = -1;
                break;

            case 40:  // Down
                delta = 1;
                break;

            default:
                return;
        }

        if (index > this.dataProvider.length -1) {
            index = this.dataProvider.length;
        }
        if (index < 0) {
            index = 0;
        }

        if (index === oldindex) {
            return false;
        }

        this.setSelectedIndex(index);

        if (this.yPosition > (index * this.itemHeight)) {
            this.yPosition = (index*this.itemHeight);
        }
        if (this.yPosition < ((index+1) * this.itemHeight) - this.$el.height()) {
            this.yPosition = ((index+1)*this.itemHeight) - this.$el.height();
        }

        this.updateLayout();
        this.cleanupTimeout = setTimeout(function() {
            self.cleanupListItems();
        }, 100);

        var target = this.$ul.find('.megalistSelected');

        setTimeout(function() {
            var event = $.Event(action, data),
                data = {
                    selectedIndex: index,
                    srcElement: $(target),
                    item: self.dataProvider[index],
                    destination: self.$el.attr('id')
                };
            self.$el.trigger(event);
        }, 150);

        return false;
    },

    /**
     * Updates megalistSide widget on mouse scroll event
     * only concerned about vertical scroll
     *
     * @param {event} event - mouse wheel event
     */
    onMouseWheel: function (event) {
        clearTimeout(this.cleanupTimeout);

        var self = this,
            orgEvent = event.originalEvent,
            delta = 0,
            totalHeight = this.dataProvider.length * this.itemHeight,
            maxPosition = totalHeight - this.$el.height();

        // Old school scrollwheel delta
        if (orgEvent.wheelDelta) {
            delta = orgEvent.wheelDelta / 120;
        }
        if (orgEvent.detail) {
            delta = -orgEvent.detail / 3;
        }

        // Webkit
        if ( orgEvent.wheelDeltaY !== undefined ) {
            delta = orgEvent.wheelDeltaY / 120;
        }

        this.yPosition -= delta * this.itemHeight;

        //limit the mouse wheel scroll area
        if (this.yPosition > maxPosition) {
            this.yPosition = maxPosition;
        }
        if (this.yPosition < 0) {
            this.yPosition = 0;
        }

        this.updateLayout();
        this.cleanupTimeout = setTimeout(function() {
            self.cleanupListItems();
        }, 100);

        return false;
    },

    /**
     * Handles click event on megalist element
     *
     * @param {event} event - mouse wheel event
     */
    processListClick: function(event) {
        var self = this,
            target = event.target,
            index = $(target).attr('list-index'),
            out_data = this.dataProvider[index],
            clicked_value = this.dataProvider[index];

        while (target.parentNode !== null) {
            if (target.nodeName === 'LI') {
                break;
            }
            target = target.parentNode;
        }

        if (target.nodeName !== 'LI') {
            return false;
        }

        if (index === this.selectedIndex) {
            return false;
        }

        this.setSelectedIndex(index);

        this.getTargetList().updateDataProvider(out_data);

        self.clearSelectedIndex();

        self.dataProviderOrig.splice(
            self.dataProviderOrig.indexOf(clicked_value), 1
        );

        if (this.yPosition > this.getMaxPosition()) {
            this.yPosition -= this.itemHeight;
        }

        self.filterList();
        this.$parent.destinationList.generatePOST(this.conf.BUILD_FULL_POST);

        return true;
    },

    /**
     * Handles click on "move all" button, move all items from one
     * megalistSide to the other, renders POST result into hidden input field
     * after the action is performed
     *
     */
    onMoveAll: function(){
        var out_data = this.dataProvider,
            i;

        this.getTargetList().updateDataProvider(out_data);

        this.clearSelectedIndex();
        this.dataProvider = [];
        if (this.filteredData.length > 0) {
            for (i = this.filteredData.length - 1; i >= 0; i--) {
                this.dataProviderOrig.splice(this.filteredData[i], 1);
            }
        } else if (!this.searchingIsActive()) {
            this.dataProviderOrig = [];
        }
        this.$parent.destinationList.generatePOST(this.conf.BUILD_FULL_POST);
        this.updateLayout();
    },

    /**
     * Handles drag event on scrollbar - binds events appropriate to user
     * action and delgates event to correct function
     *
     * @param {event} event - mouse event on scrollbar
     */
    onScrollbarStart: function(event) {
        var self = this;

        this.unbindScrollbarEvents();
        this.scrollbarInputCoordinates = this.getInputCoordinates(event);

        $(document).bind('mousemove', function(event) {
             self.onScrollbarMove(event);
        });

        $(document).bind('mouseup', function() {
             self.unbindScrollbarEvents();
        });

        event.preventDefault();
        return false;
    },

    /**
     * Handles drag event on scroll bar and recalculates what items should be
     * rendered in the viewport
     *
     * @param {event} event - scrollbar drag event to get coordinates from
     */
    onScrollbarMove: function(event) {
        var newCoordinates = this.getInputCoordinates(event),
            height = this.$el.height(),
            totalHeight = this.dataProvider.length * this.itemHeight,
            scrollbarHeight = this.$scrollbar.height(),
            yDelta = this.scrollbarInputCoordinates.y - newCoordinates.y,
            yPosition = parseInt(this.$scrollbar.css('top'), 10),
            usingMinSize = scrollbarHeight === this.conf.SCROLLBAR_MIN_SIZE,
            heightOffset = usingMinSize ? scrollbarHeight : 0,
            newYPosition;

        // valid move occurs only when pressing left mouse button
        if (event.which !== 1) {
            this.unbindScrollbarEvents();
            return;
        }

        yPosition -= yDelta;

        yPosition = Math.max(yPosition, 0);
        yPosition = Math.min(yPosition, height - scrollbarHeight);
        yPosition = Math.min(yPosition, height);

        this.$scrollbar.css('top', yPosition);
        this.scrollbarInputCoordinates = newCoordinates;

        newYPosition = (
            yPosition / (height - heightOffset) *
            (this.itemHeight * this.dataProvider.length - 1)
        );
        newYPosition = Math.max(0, newYPosition);
        newYPosition = Math.min(
            newYPosition, totalHeight - height
        );

        this.yPosition = newYPosition;
        this.updateLayout(true);

        event.preventDefault();
        return false;
    },

    /**
     * Utility function to remove events bound to the scrollbar
     *
     */
    unbindScrollbarEvents: function() {
        $(document).unbind('mousemove');
        $(document).unbind('mouseup');
    },

    /**
     * Handles click event on scrollbar background - a click on scrollbar
     * background should cause pageUp/PageDown action on the viewport
     *
     * @param {event} event - scrollbar click event to get coordinates from
     */
    onScrollbarBackgroundClick: function(event, repeatTimeout) {
        var self = this,
            // firefox uses originalEvent.layerY instead of offsetY
            yOffset = event.offsetY !== undefined ? event.offsetY : event.originalEvent.layerY,
            scrollbarBackgroundHeight = $(event.target).height(),
            clickPos = yOffset / scrollbarBackgroundHeight,
            listTotalHeight = this.dataProvider.length * this.itemHeight,
            scrollbarHeightFraction = this.$scrollbar.height() / scrollbarBackgroundHeight,
            currentPos = this.yPosition / listTotalHeight,
            offsetToMove = this.pageHeight,
            shouldMoveUp = clickPos > currentPos + scrollbarHeightFraction,
            shouldMoveDown = clickPos < currentPos;

        if (!this.scrollingActive) {
            return;
        }

        if (this.scrollDir == undefined) {
            if (shouldMoveUp) {
                this.scrollDir = 1;
            } else if (shouldMoveDown) {
                this.scrollDir = -1;
            } else {
                return;
            }
        }

        if (shouldMoveUp && this.scrollDir === 1) {
            this.yPosition += offsetToMove;
        } else if (shouldMoveDown && this.scrollDir === -1) {
            this.yPosition -= offsetToMove;
        } else {
            return;
        }

        if (this.yPosition > listTotalHeight - this.pageHeight) {
            this.yPosition = listTotalHeight - this.pageHeight;
        } else if (this.yPosition < 0) {
            this.yPosition = 0;
        }

        this.updateLayout();

        if (this.scrollingActive) {
            if (repeatTimeout === undefined) {
                repeatTimeout = this.conf.CONTINOUS_SCROLLING_FIRST_INTERVAL;
            }
            setTimeout(function() {
                self.onScrollbarBackgroundClick(
                    event, self.conf.CONTINOUS_SCROLLING_INTERVAL
                );
            }, repeatTimeout);
        }
    },

    /**
     * Removes items rendered in megalist that no longer fit into the viewport
     * and removes them from processed items cache
     */
    cleanupListItems: function() {
        //remove any remaining LI elements hanging out on the dom
        var temp = [],
            item, index, x;

        for (x = 0; x < this.totalItems.length; x++ ) {
            item = this.totalItems[x];
            index = item.attr('list-index');
            if (this.processedItems[index] === undefined) {
                item.remove();
            }
        }
        //cleanup processedItems array
        if (this.processedItems) {
            for (index in this.processedItems) {
                temp.push(this.processedItems[index]);
            }
        }
        this.totalItems = temp;
    },

    /**
     * Extracts input coordinates from the event
     *
     * @param {event} event - event to get coordinates from
     * @return {object} result - object containge x and y coordinates
     */
    getInputCoordinates: function (event) {
        var targetEvent = event,
            result = {
                x: Math.round(targetEvent.pageX),
                y: Math.round(targetEvent.pageY)
            };
        return result;
    },

    /**
     * Main rendering function for megalist: redraws the list based on data
     * fed to megalist and scrollbar position. Iterates over visible items
     * and renders them then calls update on the scrollbar if ignoreScrollbar
     * not set to true
     *
     * @param {boolean} ignoreScrollbar - a flag allowing scrollbar to not be
     * redrawn if not necessary
     */
    updateLayout: function(ignoreScrollbar) {
        var height = this.$el.height(),
            i = -1,
            startPosition = Math.ceil(this.yPosition / this.itemHeight),
            maxHeight = 2 * (height + (2 * this.itemHeight)),
            index, item, currentPosition, parentLength;

        if (this.dataProvider.length > 0) {
            this.$ul.detach();
            this.processedItems = {};

            while (i * this.itemHeight < maxHeight) {
                index = Math.min(
                    Math.max(startPosition + i, 0),
                    this.dataProvider.length
                );

                item = this.getItemAtIndex(index);
                this.totalItems.push(item);

                this.processedItems[index.toString()] = item;
                currentPosition = i * this.itemHeight;
                this.setItemPosition(item, 0, currentPosition);

                if (item.parent().length <= 0) {
                    this.$ul.append(item);

                    if (this.itemHeight <= 0) {
                        this.prepareLayout(item);
                        this.updateLayout();
                        return;
                    }
                }
                i++;
            }

            this.cleanupListItems();
            if (ignoreScrollbar !== true) {
                this.updateScrollBar();
            }
            if (this.$scrollbar.parent().length > 0){
                this.$scrollbar.before(this.$ul);
            } else {
                 this.$el.append(this.$ul);
            }
        } else {
            if (this.$ul.children().length > 0) {
                this.$ul.empty();
                this.cleanupListItems();
                parentLength = this.$scrollbar.parent().length > 0;
                if (ignoreScrollbar !== true && parentLength > 0) {
                    this.updateScrollBar();
                }
            } else {
                this.hideScrollbar();
            }
        }
    },

    /**
     * Prepares layout by appending list to DOM, and calculating site of
     * element and size of single page
     *
     * @param  {object} item    jQuery object representing single item
     */
    prepareLayout: function(item) {
        var itemsPerPage;

        // make sure item have proper height by filling it with content
        item.html('&nsbp;');
        this.$el.append(this.$ul);

        // calculate height of item and height of single page
        this.itemHeight = item.outerHeight();
        itemsPerPage = Math.floor(
            this.$ul.parent().height() / this.itemHeight
        );
        this.pageHeight = this.itemHeight * itemsPerPage;
    },

    /**
     * Shows scrollbar
     */
    showScrollbar: function() {
        this.$el.append(this.$scrollbar, this.$scrollbarBackground);
    },

    /**
     * Hides scrollbar
     */
    hideScrollbar: function() {
        this.$scrollbar.detach();
        this.$scrollbarBackground.detach();
    },

    /**
     * Renders the scrollbar as a part of UI update when list is scrolled or
     * modified
     */
    updateScrollBar: function() {
        var height = this.$el.height(),
            maxScrollbarHeight = height,
            maxItemsHeight = this.dataProvider.length * this.itemHeight,
            targetHeight = maxScrollbarHeight * Math.min(
                maxScrollbarHeight / maxItemsHeight, 1
            ),
            actualHeight = Math.floor(
                Math.max(targetHeight, this.conf.SCROLLBAR_MIN_SIZE)
            ),
            scrollPosition = (
                this.yPosition / (maxItemsHeight - height) *
                (maxScrollbarHeight - actualHeight)
            ),
            parent = this.$scrollbar.parent();

        if (scrollPosition < 0) {
            actualHeight = Math.max(actualHeight + scrollPosition, 0);
            scrollPosition = 0;
        } else if (scrollPosition > (height - actualHeight)) {
            actualHeight = Math.min(actualHeight, height - scrollPosition);
        }

        this.$scrollbar.height(actualHeight);

        if ((this.dataProvider.length * this.itemHeight) <= height) {
            if (parent.length > 0) {
                this.hideScrollbar();
            }
        } else {
            if (parent.length <= 0) {
                this.showScrollbar();
            }
            this.$scrollbar.css('top', scrollPosition);
        }
    },

    /**
     * Utility function to set offset css on an item
     *
     * @param {object} item - megalist element
     * @param {int} x - x offset in pixels
     * @param {int} y - y offset in pixels
     */
    setItemPosition: function(item, x, y) {
        item.css('left', x);
        item.css('top', y);
    },

    /**
     * Gets megalist item at given index. Parses it to <li> item if necessary
     *
     * @param {int} i - object index
     * @return {object} - jQuery object containing selected <li> element
     */
    getItemAtIndex: function(i) {
        var item, iString, data;
        if (this.dataProvider === this.listItems) {
            item = $(this.listItems[i]);
        }
        else if (i !== undefined){
            iString = i.toString();

            if (this.listItems[iString] === null ||
                this.listItems[iString] === undefined
            ) {
                item = $('<li />');
                this.listItems[iString] = item;
            } else {
                item = $(this.listItems[i]);
            }

            if (i >= 0 && i < this.dataProvider.length){
                data = this.dataProvider[i];
                item.html(data.label);
                item.attr('list-value', data.listValue);
            }
        }
        if (item !== null && item !== undefined) {
            item.attr('list-index', i);
        }
        return item;
    },

    /**
     * Returns index of currently selected item
     *
     * @return {int} - index of item that was selected
     */
    getSelectedIndex: function() {
        return parseInt(this.selectedIndex, 10);
    },

    /**
     * Sets item at given index as selected and adds appropriate styling to it
     *
     * @param {int} index = index of item that was selected
     */
    setSelectedIndex: function(index) {
        var item = this.getItemAtIndex(this.selectedIndex);

        if (item !== undefined) {
            item.removeClass('megalistSelected');
        }

        this.selectedIndex = index;
        this.getItemAtIndex(index).addClass('megalistSelected');
    },

    /**
     * Clears currently selected object by removing styling and setting
     * internal variable pointing to currently selected item to -1
     *
     */
    clearSelectedIndex: function() {
        var item = this.getItemAtIndex(this.selectedIndex);

        if (item !== undefined) {
            item.removeClass('megalistSelected');
        }
        this.selectedIndex = -1;
    },

    /**
     * Sets initial data for megalist and updates layout with it
     *
     * @param {Array} dataProvider - object array to initially feed megalist
     */
    setDataProvider: function(dataProvider) {
        this.clearSelectedIndex();
        this.dataProviderOrig = dataProvider;
        this.dataProvider = dataProvider;

        this.$ul.find('li').each(function() {
            $(this).remove();
        });

        this.yPosition = 0;
        this.updateLayout();
    },

    /**
     * Updates megalist with new data. Accepts either a single object or
     * an Array of objects and updates layout with new data
     *
     * @param {object|Array} newElement - new object / array of objects
     *                                    to be inserted into the list
     */
    updateDataProvider: function(newElement) {
        this.clearSelectedIndex();

        if ($.isArray(newElement)) {
            $.merge(this.dataProviderOrig, newElement);
        } else {
            this.dataProviderOrig.push(newElement);
        }
        this.filterList();

        this.$ul.find('li').each(function() {
            $(this).remove();
        });

        this.yPosition = this.getMaxPosition();
        this.updateLayout();
    },

    /**
     * Returns current objects in megalist
     *
     * @return {Array} - list of objects in megalist
     *
     */
    getDataProvider: function() {
        return this.dataProvider;
    },

    /**
     * Get maximum value of yPosition
     *
     * @return {int} maximum value of yPosition
     */
    getMaxPosition: function() {
        var height = this.$el.height(),
            totalHeight = this.dataProvider.length * this.itemHeight;

        return totalHeight > height ? totalHeight - height : 0;
    },

    /**
     * Checks if search input has minimal length and therefor searching  is
     * active.
     * @return {bool} true when searching is active, false otherwise
     */
    searchingIsActive: function() {
        var querySize = $.trim(this.$search.val()).length;
        return querySize >= this.conf.MINIMUM_SEARCH_QUERY_SIZE;
    },

    /**
     * Parses search input and performs filtering of list. The algorithm
     * splits the search query to tokens and seeks for all subsequent
     * tokens in the data. If not all tokens are found in the data then this
     * record is excluded from the results.
     *
     */
    filterList: function() {
        var self = this,
            searchQuery = $.trim(this.$search.val().toLowerCase()),
            searchTokens = searchQuery.split(' '),
            i;

        this.filteredData = [];

        for (i = searchTokens.length - 1; i >= 0; i--) {
            searchTokens[i] = $.trim(searchTokens[i]);
        }

        if (!this.searchingIsActive()) {
            this.dataProvider = this.dataProviderOrig;

        } else {
            this.dataProvider = $.grep(
                this.dataProviderOrig,
                function(val, index) {
                    return self.testListElement(val, searchTokens, index);
                }
            );
        }

        this.updateLayout();
    },

    /**
     * Tests if element of list data meets the query search criterias.
     *
     * @param  {string} val          value of the element to test
     * @param  {array}  searchTokens query search tokens
     * @param  {int}    index        the index of element in original data
     *
     * @return {boolean}             whether element meets the criteria on not
     */
    testListElement: function(val, searchTokens, index) {
        var tokenIndex = 0,
            valI = 0,
            tokenDetected = true,
            i;
        val = val.label.toLowerCase();
        while (valI < val.length) {
            if (val[valI++] === searchTokens[tokenIndex][0]) {
                tokenDetected = true;
                for (i = 1; i < searchTokens[tokenIndex].length; i++) {
                    if (val[valI] === searchTokens[tokenIndex][i]) {
                        valI++;
                    } else {
                        tokenDetected = false;
                        break;
                    }
                }
                if (tokenDetected && ++tokenIndex === searchTokens.length) {
                    this.filteredData[this.filteredData.length] = index;
                    return true;
                }
            }
        }
        return false;
    },

    /**
     * Generates string result of what is currently selected and populates
     * this.$input value, adding it to DOM id necessary. Only does it for
     * destination list. Result can be in 2 formats: POST-like (full) or comma
     * separated
     *
     * @param {boolean} full - wherever to generate full POST-like data
     * @return {string} result - string result of what is currently selected
     */
    generatePOST: function(full) {
      var i,
          postData = [],
          result = {},
          name = this.name;

      if (this.suffix === this.conf.DESTINATION_SUFFIX){
          for (i = 0; i < this.dataProviderOrig.length; i++) {
              postData[i] = this.dataProviderOrig[i].listValue;
          }
          if (full === true){
              result[name] = postData;
              result = decodeURIComponent($.param(result, true ));
              //cut out first name so that the post will not contain repetition
              result = result.slice(this.name.length + 1, result.length);
              this.$input.val(result);
          } else {
              result = postData.join(',');
              this.$input.val(result);
          }

          if (this.$el.has(this.$input).length < 1) {
              this.$el.append(this.$input);
          }
          return result;
      } else {
          return '';
      }
    }

  };

  /* LIST PLUGIN DEFINITION
   * ========================== */

  $.fn.megalist = function (option, params) {
    if (typeof option === 'object') { this.options = option;}
    var multiselect = new Megalist(this);
    if (typeof option === 'string') { this.result = multiselect[option](params); }
    return this;
  };

  // injects svg arrow icons into dom
  $(document).ready(function(){
    $('body').append('<svg style="display: none" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"> <path id="arrow-left" d="M48 10.667q1.104 0 1.885 0.781t0.781 1.885-0.792 1.896l-16.771 16.771 16.771 16.771q0.792 0.792 0.792 1.896t-0.781 1.885-1.885 0.781q-1.125 0-1.896-0.771l-18.667-18.667q-0.771-0.771-0.771-1.896t0.771-1.896l18.667-18.667q0.771-0.771 1.896-0.771zM32 10.667q1.104 0 1.885 0.781t0.781 1.885-0.792 1.896l-16.771 16.771 16.771 16.771q0.792 0.792 0.792 1.896t-0.781 1.885-1.885 0.781q-1.125 0-1.896-0.771l-18.667-18.667q-0.771-0.771-0.771-1.896t0.771-1.896l18.667-18.667q0.771-0.771 1.896-0.771z"></path> <path id="arrow-right" d="M29.333 10.667q1.104 0 1.875 0.771l18.667 18.667q0.792 0.792 0.792 1.896t-0.792 1.896l-18.667 18.667q-0.771 0.771-1.875 0.771t-1.885-0.781-0.781-1.885q0-1.125 0.771-1.896l16.771-16.771-16.771-16.771q-0.771-0.771-0.771-1.896 0-1.146 0.76-1.906t1.906-0.76zM13.333 10.667q1.104 0 1.875 0.771l18.667 18.667q0.792 0.792 0.792 1.896t-0.792 1.896l-18.667 18.667q-0.771 0.771-1.875 0.771t-1.885-0.781-0.781-1.885q0-1.125 0.771-1.896l16.771-16.771-16.771-16.771q-0.771-0.771-0.771-1.896 0-1.146 0.76-1.906t1.906-0.76z"></path></svg>');});

  //adds indexOf to arry prototype for ie8
  if(!Array.prototype.indexOf){Array.prototype.indexOf=function(e){var t=this.length>>>0;var n=Number(arguments[1])||0;n=n<0?Math.ceil(n):Math.floor(n);if(n<0)n+=t;for(;n<t;n++){if(n in this&&this[n]===e)return n}return-1}}

} (window.jQuery);
