module.exports = {
    testEnvironment: "jsdom",
    automock: false,
    collectCoverageFrom: [
        '**/hypha/static_src/src/app/src/**.{js}',
        '!**/tests/**',
    ],
    roots: ['.'],
    testPathIgnorePatterns: [
        '/node_modules/',
        '/dist/',
        '/__tests__/data/',
        '/lib/',
        '/static/'
    ],
    moduleNameMapper: {
        '\\.(css|less|scss)$': 'identity-obj-proxy',

        '@common(.*)$': '<rootDir>/hypha/static_src/src/app/src/common$1',
        '@components(.*)$': '<rootDir>/hypha/static_src/src/app/src/components$1',
        '@containers(.*)$': '<rootDir>/hypha/static_src/src/app/src/containers$1',
        '@redux/(.*)$': '<rootDir>/hypha/static_src/src/app/src/redux/$1',
        '@reducers(.*)$': '<rootDir>/hypha/static_src/src/app/src/redux/reducers$1',
        '@selectors(.*)$': '<rootDir>/hypha/static_src/src/app/src/redux/selectors$1',
        '@actions(.*)$': '<rootDir>/hypha/static_src/src/app/src/redux/actions$1',
        '@middleware(.*)$': '<rootDir>/hypha/static_src/src/app/src/redux/middleware$1',

        '@api(.*)$': '<rootDir>/hypha/static_src/src/app/src/api$1',
        '@utils(.*)$': '<rootDir>/hypha/static_src/src/app/src/utils$1'

     
    },
    setupFiles: [
        '<rootDir>/jestSetup.js'
    ],
    moduleFileExtensions: [
        'ts',
        'tsx',
        'js',
        'json'
    ],
    unmockedModulePathPatterns: [
        'react',
        'react-native',
        'enzyme',
        'chai',
        'react-addons-test-utils',
        'rxjs'
    ],
    snapshotSerializers: [
        'enzyme-to-json/serializer'
    ],
    coverageDirectory: '<rootDir>/__coverage__',
    verbose: true,
    testURL: 'http://localhost/'
};
