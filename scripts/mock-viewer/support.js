/*
 * Development tool only (D-046). A small stand-in for the design tool's runtime, so that the files in
 * docs/mocks/source/ can be opened in a browser and compared with the app. It is never part of the app.
 *
 * It supports exactly what the mocks use: <x-dc>, <helmet>, <sc-for>, <sc-if>, <dc-import>,
 * {{dotted.path}} bindings, and a component class that extends DCLogic.
 */
(function () {
  "use strict";

  var BOOLEAN_ATTRIBUTES = ["disabled", "checked", "hidden", "readonly", "open", "selected", "autofocus"];
  var WHOLE = /^\s*\{\{\s*([\w$.]+)\s*\}\}\s*$/;
  var PART = /\{\{\s*([\w$.]+)\s*\}\}/g;

  var files = {};
  var instances = {};
  var addedStyles = {};
  var pending = false;
  var mounted = false;
  var rootName = decodeURIComponent(location.pathname.split("/").pop()).replace(/\.dc\.html$/, "");

  window.__mockErrors = [];
  function report(error) {
    window.__mockErrors.push(String((error && error.stack) || error));
    console.error(error);
  }

  function DCLogic(props) {
    this.props = props || {};
    this.state = {};
  }
  DCLogic.prototype.setState = function (change) {
    var next = typeof change === "function" ? change(this.state, this.props) : change;
    this.state = Object.assign({}, this.state, next);
    schedule();
  };
  DCLogic.prototype.forceUpdate = function () {
    schedule();
  };

  function load(name) {
    if (files[name]) return files[name];
    var request = new XMLHttpRequest();
    request.open("GET", "./" + name + ".dc.html", false);
    request.send();
    if (request.status !== 200) throw new Error("Mock not found: " + name);

    // <template> may appear anywhere (even inside tables), so loops and conditions are parsed as templates.
    var source = request.responseText
      .replace(/<sc-(for|if)(?=[\s>])/g, '<template data-sc="$1"')
      .replace(/<\/sc-(for|if)>/g, "</template>");
    var parsed = new DOMParser().parseFromString(source, "text/html");
    var root = parsed.querySelector("x-dc");
    if (!root) throw new Error("No <x-dc> in " + name);

    var helmet = root.querySelector("helmet");
    if (helmet) {
      Array.prototype.forEach.call(helmet.children, function (child) {
        var key = child.outerHTML;
        if (!addedStyles[key]) {
          addedStyles[key] = true;
          document.head.appendChild(document.importNode(child, true));
        }
      });
      helmet.remove();
    }

    var script = parsed.querySelector("script[data-dc-script]");
    var defaults = {};
    var Component = null;
    if (script) {
      var declared = JSON.parse(script.getAttribute("data-props") || "{}");
      Object.keys(declared).forEach(function (key) {
        if (key.charAt(0) !== "$" && "default" in declared[key]) defaults[key] = declared[key]["default"];
      });
      Component = new Function("DCLogic", script.textContent + "\nreturn Component;")(DCLogic);
    }
    files[name] = { nodes: root.childNodes, Component: Component, defaults: defaults };
    return files[name];
  }

  function lookup(scope, path) {
    var parts = path.split(".");
    var value = scope;
    for (var i = 0; i < parts.length; i++) {
      if (value === null || value === undefined) return undefined;
      value = value[parts[i]];
    }
    return value;
  }

  function fill(text, scope) {
    return text.replace(PART, function (_match, path) {
      var value = lookup(scope, path);
      return value === null || value === undefined || value === false ? "" : String(value);
    });
  }

  function value(text, scope) {
    var whole = WHOLE.exec(text);
    return whole ? lookup(scope, whole[1]) : fill(text, scope);
  }

  function renderChildren(nodes, scope, target, key) {
    Array.prototype.forEach.call(nodes, function (node, index) {
      renderNode(node, scope, target, key + "." + index);
    });
  }

  function renderNode(node, scope, target, key) {
    if (node.nodeType === 3) {
      target.appendChild(document.createTextNode(fill(node.nodeValue, scope)));
      return;
    }
    if (node.nodeType !== 1) return;

    var directive = node.localName === "template" ? node.getAttribute("data-sc") : null;
    if (directive === "if") {
      if (value(node.getAttribute("value") || "", scope)) renderChildren(node.content.childNodes, scope, target, key);
      return;
    }
    if (directive === "for") {
      var list = value(node.getAttribute("list") || "", scope) || [];
      var as = node.getAttribute("as") || "item";
      Array.prototype.forEach.call(list, function (item, index) {
        var inner = Object.create(scope);
        inner[as] = item;
        inner.$index = index;
        renderChildren(node.content.childNodes, inner, target, key + "[" + index + "]");
      });
      return;
    }
    if (node.localName === "dc-import") {
      var props = {};
      Array.prototype.forEach.call(node.attributes, function (attribute) {
        if (attribute.name !== "name" && attribute.name.indexOf("hint-") !== 0) {
          props[attribute.name] = value(attribute.value, scope);
        }
      });
      var holder = document.createElement("div");
      holder.style.display = "contents";
      target.appendChild(holder);
      renderComponent(node.getAttribute("name"), props, holder, key);
      return;
    }

    var element = document.importNode(node, false);
    var formValue;
    Array.prototype.slice.call(element.attributes).forEach(function (attribute) {
      var name = attribute.name;
      if (name.indexOf("hint-") === 0) {
        element.removeAttribute(name);
        return;
      }
      if (attribute.value.indexOf("{{") < 0) return;
      var result = value(attribute.value, scope);
      if (name.indexOf("on") === 0) {
        element.removeAttribute(name);
        if (typeof result === "function") {
          var event = name === "onchange" ? "input" : name.slice(2);
          element.addEventListener(event, result);
        }
      } else if (BOOLEAN_ATTRIBUTES.indexOf(name) >= 0) {
        if (result) element.setAttribute(name, "");
        else element.removeAttribute(name);
      } else if (result === undefined || result === null || (result === false && name.indexOf("aria-") !== 0)) {
        element.removeAttribute(name);
      } else {
        element.setAttribute(name, String(result));
        if (name === "value") formValue = String(result);
      }
    });
    target.appendChild(element);
    renderChildren(node.childNodes, scope, element, key);
    if (formValue !== undefined) element.value = formValue;
  }

  function renderComponent(name, props, target, key) {
    var file = load(name);
    var merged = Object.assign({}, file.defaults, props);
    var scope = Object.create(null);
    if (file.Component) {
      var id = key + ":" + name;
      var instance = instances[id];
      if (!instance) {
        instance = instances[id] = { logic: new file.Component(merged), isNew: true };
      }
      instance.logic.props = merged;
      var values = instance.logic.renderVals ? instance.logic.renderVals() : {};
      Object.assign(scope, merged, values);
    } else {
      Object.assign(scope, merged);
    }
    renderChildren(file.nodes, scope, target, key + ">" + name);
  }

  function render() {
    pending = false;
    try {
      var host = document.getElementById("mock-root");
      var next = document.createDocumentFragment();
      var query = {};
      new URLSearchParams(location.search).forEach(function (v, k) {
        query[k] = v;
      });
      renderComponent(rootName, query, next, "root");
      host.replaceChildren(next);
      Object.keys(instances).forEach(function (id) {
        var instance = instances[id];
        var logic = instance.logic;
        if (instance.isNew) {
          instance.isNew = false;
          if (logic.componentDidMount) logic.componentDidMount();
        } else if (mounted && logic.componentDidUpdate) {
          logic.componentDidUpdate(logic.props, logic.state);
        }
      });
      mounted = true;
    } catch (error) {
      report(error);
    }
    window.__mockReady = true;
  }

  function schedule() {
    if (pending) return;
    pending = true;
    window.setTimeout(render, 0);
  }

  window.addEventListener("error", function (event) {
    report(event.error || event.message);
  });

  document.addEventListener("DOMContentLoaded", function () {
    var original = document.querySelector("x-dc");
    if (original) original.remove();
    var host = document.createElement("div");
    host.id = "mock-root";
    document.body.appendChild(host);
    render();
  });
})();
