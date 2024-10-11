import globals from "globals";
import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import jsdoc from "eslint-plugin-jsdoc";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all,
});

export default [
    {
        ignores: ["**/*.min.js", "**/esm/*.js"],
    },
    ...compat.extends("eslint:recommended", "prettier"),
    jsdoc.configs["flat/recommended"],
    {
        languageOptions: {
            globals: {
                ...globals.browser,
                ...globals.commonjs,
                jQuery: true,
            },
        },

        plugins: {
            jsdoc,
        },

        rules: {
            "array-bracket-spacing": ["error", "never"],
            "block-scoped-var": "error",
            "comma-spacing": "error",
            "comma-style": ["error", "last"],
            "computed-property-spacing": ["error", "never"],
            curly: ["error", "all"],
            "eol-last": "error",
            eqeqeq: ["error", "smart"],
            "guard-for-in": "error",

            "key-spacing": [
                "error",
                {
                    beforeColon: false,
                    afterColon: true,
                },
            ],

            "keyword-spacing": [
                "error",
                {
                    before: true,
                    after: true,
                },
            ],

            "linebreak-style": ["error", "unix"],

            "lines-around-comment": [
                "error",
                {
                    beforeBlockComment: true,
                    afterBlockComment: false,
                },
            ],

            "new-parens": "error",
            "no-array-constructor": "error",
            "no-caller": "error",
            "no-catch-shadow": "error",
            "no-eval": "error",
            "no-extend-native": "error",
            "no-extra-bind": "error",
            "no-extra-parens": ["error", "functions"],
            "no-implied-eval": "error",
            "no-iterator": "error",
            "no-label-var": "error",
            "no-labels": "error",
            "no-lone-blocks": "error",
            "no-loop-func": "error",
            "no-multi-spaces": "error",
            "no-multi-str": "error",
            "no-native-reassign": "error",
            "no-nested-ternary": "error",
            "no-new-func": "error",
            "no-new-object": "error",
            "no-new-wrappers": "error",
            "no-octal-escape": "error",
            "no-process-exit": "error",
            "no-proto": "error",
            "no-return-assign": "error",
            "no-script-url": "error",
            "no-sequences": "error",
            "no-shadow-restricted-names": "error",
            "no-spaced-func": "error",
            "no-trailing-spaces": "error",
            "no-undef-init": "error",
            "no-undefined": "error",
            "no-unused-expressions": "error",

            "no-unused-vars": [
                "error",
                {
                    vars: "all",
                    args: "none",
                },
            ],

            "no-with": "error",
            "one-var": ["error", "never"],
            semi: ["error", "always"],

            "semi-spacing": [
                "error",
                {
                    before: false,
                    after: true,
                },
            ],

            "space-before-blocks": ["error", "always"],

            "space-before-function-paren": [
                "error",
                {
                    anonymous: "always",
                    named: "never",
                },
            ],

            "space-in-parens": ["error", "never"],
            "space-infix-ops": "error",

            "space-unary-ops": [
                "error",
                {
                    words: true,
                    nonwords: false,
                },
            ],

            "spaced-comment": ["error", "always"],
            strict: ["error", "function"],
            yoda: ["error", "never"],
            "max-nested-callbacks": ["warn", 3],
            "jsdoc/require-description": "warn",
            "jsdoc/tag-lines": ["off", "never"],
        },
    },
];
