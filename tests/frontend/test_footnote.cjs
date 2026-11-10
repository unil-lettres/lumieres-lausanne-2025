// Run with node tests/frontend/test_footnote.cjs [plugin-path]. No browser/database needed.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(process.argv[2] || path.resolve(__dirname, '../../app/ckeditor/static/ckeditor/ckeditor/plugins/footnote/plugin.js'), 'utf8');
for (const language of ['fr', 'en']) {
  let plugin, factory;
  const context = { CKEDITOR: {
    plugins: { add: (_, definition) => { plugin = definition; } },
    dialogCommand: function () {}, dialog: { add: (_, definition) => { factory = definition; } },
  }};
  vm.runInNewContext(source, context);
  const editor = { config: { language }, addCommand() {}, ui: { addButton() {} } };
  plugin.init(editor);
  const field = factory(editor).contents[0].elements.find(e => e.id === 'place');
  let value;
  const control = { setValue(v) { value = v; }, getValue() { return value; } };
  for (const [existing, expected] of [[null, 'note-editorial'], ['', 'note-editorial'], ['note-editorial', 'note-editorial'], ['note-document', 'note-document']]) {
    field.setup.call(control, { getAttribute: () => existing });
    assert.equal(value, expected);
    assert.equal(field.validate.call(control), true);
    let saved;
    field.commit.call(control, { setAttribute: (key, v) => { assert.equal(key, 'class'); saved = v; } });
    assert.equal(saved, expected);
  }
  for (const invalid of ['', null, 'unexpected', 'note-editorial extra']) {
    value = invalid;
    const message = field.validate.call(control);
    assert.equal(typeof message, 'string');
    assert.ok(message.length > 0);
  }
}
console.log('Footnote type checks passed in FR/EN: defaults, preservation, commit, invalid values.');
