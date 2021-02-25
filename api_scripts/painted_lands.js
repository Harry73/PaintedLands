var PaintedLands = PaintedLands || (function () {
    'use strict';


    // ################################################################################################################
    // Constants


    const NAMESPACE = 'PaintedLands';


    // ################################################################################################################
    // State


    let SAVED_ACTIONS = {};


    // ################################################################################################################
    // Assertions


    function assert(condition, message, ...rest) {
        if (condition === undefined || condition === null) {
            throw 'assert() missing condition';
        }
        if (message === undefined || message === null) {
            throw 'assert() missing message';
        }

        if (!condition) {
            throw message.format(...rest);
        }
    }


    function assert_not_null(parameter, message) {
        if (message === undefined || message === null) {
            throw 'assert_not_null() missing message';
        }

        assert(parameter !== undefined, 'AssertionError: ' + message);
        assert(parameter !== null, 'AssertionError: ' + message);
    }


    // ################################################################################################################
    // Logging


    const LogLevel = {
        TRACE: 0,
        DEBUG: 1,
        INFO: 2,
        WARN: 3,
        ERROR: 4,
    };


    class LOG {
        static _log(log_level, string) {
            assert_not_null(log_level, '_log() log_level');
            assert_not_null(string, '_log() string');

            if (log_level >= this.level) {
                log(string);
            }
        }

        static trace(string) {
            this._log(LogLevel.TRACE, string);
        }

        static debug(string) {
            this._log(LogLevel.DEBUG, string);
        }

        static info(string) {
            this._log(LogLevel.INFO, string);
        }

        static warn(string) {
            this._log(LogLevel.WARN, string);
        }

        static error(string) {
            this._log(LogLevel.ERROR, string);
            sendChat('API', string);
        }
    }
    LOG.level = LogLevel.INFO;


    // ################################################################################################################
    // Functional


    // Basic python-like string formatting
    String.prototype.format = function () {
        let a = this;
        for (let i = 0; i < arguments.length; i++) {
            a = a.replace('%s', arguments[i]);
        }
        return a;
    };


    function chat(sender, message, handler) {
        assert_not_null(sender, 'raw_chat() sender');
        assert_not_null(message, 'raw_chat() message');

        sendChat(sender, message, handler);
    }



    // ################################################################################################################
    // Command handling


    function save_combat_action(msg) {
        let pieces = msg.content.split(' ');
        let text = pieces.slice(2).join(' ');

        let player = '';
        let action = '';
        if (text.includes('|')) {
            pieces = text.split('|');
            player = pieces[0];
            action = pieces[1];
        } else {
            player = msg.who;
            action = text;
        }

        const button_section = " {{button=<a href='!pl act %s|%s'>Show Action</a>}}".format(player, action);
        const response = '&{template:PaintedLands} {{name=%s Readies an Action}} %s'.format(player, button_section);
        LOG.info('Save action: ' + response);
        SAVED_ACTIONS[player] = action;
        chat(player, response);
    }


    function show_action(msg) {
        let pieces = msg.content.split(' ');
        pieces = pieces.slice(2).join(' ');
        pieces = pieces.split('|');
        const player = pieces[0];
        const action = pieces[1];

        LOG.info('%s perform action: %s'.format(player, action));
        chat(player, action);
    }


    function execute_combat() {
        const players = Object.keys(SAVED_ACTIONS);
        let response = '\n';
        for (let i = 0; i < players.length; i++) {
            const player = players[i];
            const action = SAVED_ACTIONS[player];
            response += '%s: %s\n'.format(player, action);
        }

        SAVED_ACTIONS = {};
        chat(NAMESPACE, response);
    }


    // ################################################################################################################
    // Basic setup and message handling


    const subcommands = {
        'combat': save_combat_action,
        'act': show_action,
        'execute': execute_combat,
    };


    function handle_input(msg) {
        if (!msg.content.startsWith('!')) {
            return
        }

        // Regular API call
        const pieces = msg.content.split(' ');
        if (pieces.length < 2) {
            raw_chat(NAMESPACE, 'Missing PaintedLands subcommand');
            return;
        }

        const main_command = pieces[0];
        if ('!pl' !== main_command) {
            return;
        }

        const subcommand = pieces[1];
        if (!(subcommand in subcommands)) {
            chat(NAMESPACE, 'Unknown PaintedLands subcommand %s'.format(subcommand));
            return;
        }

        const processor = subcommands[subcommand];

        try {
            processor(msg);
        } catch (err) {
            if (Object.prototype.toString.call(err) === '[object String]') {
                chat(NAMESPACE, err);
            } else {
                throw err;
            }
        }
    }


    const register_event_handlers = function () {
        on('chat:message', handle_input);
        LOG.info('PaintedLands API ready');
    };


    return {
        register_event_handlers,
    };
})();


on('ready', () => {
    'use strict';

    PaintedLands.register_event_handlers();
});
