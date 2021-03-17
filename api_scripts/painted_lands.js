var PaintedLands = PaintedLands || (function () {
    'use strict';

    // ################################################################################################################
    // Constants
    //

    const NAMESPACE = 'PaintedLands';

    // ################################################################################################################
    // State
    //

    let SAVED_ACTIONS = [];

    // ################################################################################################################
    // Assertions
    //

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
    // Functional
    //

    // Basic python-like string formatting
    String.prototype.format = function () {
        let a = this;
        for (let i = 0; i < arguments.length; i++) {
            a = a.replace('%s', arguments[i]);
        }
        return a;
    };

    // Always specifying a radix is safest, and we always want radix 10.
    function parse_int(string) {
        assert_not_null(string, 'parse_int() string');

        return parseInt(string, 10);
    }

    // Wrapper around sending chat messages with null checks
    function chat(sender, message, handler) {
        assert_not_null(sender, 'chat() sender');
        assert_not_null(message, 'chat() message');

        sendChat(sender, message, handler);
    }

    // ################################################################################################################
    // Logging utility
    //   For those more familiar with "LOG.<level>(message)" style logging.
    //

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
            chat(NAMESPACE, string);
        }
    }
    LOG.level = LogLevel.INFO;

    // ################################################################################################################
    // Command handling
    //

    function save_combat_action(msg) {
        let pieces = msg.content.split(' ');
        let text = pieces.slice(2).join(' ');

        let entity, poise, action;
        pieces = text.split('|');
        if (pieces.length === 2) {
            entity = msg.who;
            poise = pieces[0];
            action = pieces[1];
        } else if (pieces.length === 3) {
            entity = pieces[0];
            poise = pieces[1];
            action = pieces[2];
        } else {
            chat(NAMESPACE, 'Unexpected number of arguments %s for "!pl combat" command'.format(pieces.length));
            return;
        }

        if (Number.isNaN(parse_int(poise))) {
            chat(NAMESPACE, 'Non-numeric poise "%s"'.format(poise));
            return;
        }
        poise = parse_int(poise);

        // Colons do weird things to the button, get rid of them
        action = action.replace(/:/g, ';');

        const button_section = " {{button=<a href='!pl act %s|%s|%s'>Show Action</a>}}".format(entity, poise, action);
        const response = '&{template:PaintedLands} {{name=%s is Ready}} {{poise=%s}} %s'.format(
            entity, poise, button_section);
        LOG.info('Save action: ' + response);
        SAVED_ACTIONS.push({
            'entity': entity,
            'poise': poise,
            'action': action,
        });
        chat(entity, response);
    }

    function show_action(msg) {
        let pieces = msg.content.split(' ');
        pieces = pieces.slice(2).join(' ');
        pieces = pieces.split('|');
        const entity = pieces[0];
        const poise = pieces[1];
        const action = pieces[2];

        let response = '<tr>';
        response += '<td>%s</td>'.format(entity);
        response += '<td>%s</td>'.format(poise);
        response += '<td>%s</td>'.format(action);
        response += '</tr>';
        response = '&{template:PaintedLands} {{name=Action}} {{actions=%s}}'.format(response);

        LOG.info('Show action: ' + response);
        chat(NAMESPACE, response);
    }

    function execute_combat() {
        // Order actions by poise - higher poise goes first
        SAVED_ACTIONS.sort(function(a, b) {
            return b.poise - a.poise;
        });

        let response = '';
        for (let i = 0; i < SAVED_ACTIONS.length; i++) {
            const saved_action = SAVED_ACTIONS[i];
            response += '<tr>';
            response += '<td>%s</td>'.format(saved_action.entity);
            response += '<td>%s</td>'.format(saved_action.poise);
            response += '<td>%s</td>'.format(saved_action.action);
            response += '</tr>';
        }
        response = '&{template:PaintedLands} {{name=Combat Round}} {{actions=%s}}'.format(response);

        LOG.info('Combat round' + response);
        SAVED_ACTIONS = [];
        chat(NAMESPACE, response);
    }

    // ################################################################################################################
    // Message handling
    //

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
            chat(NAMESPACE, 'Missing PaintedLands subcommand');
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

    // ################################################################################################################
    // API setup
    //

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
