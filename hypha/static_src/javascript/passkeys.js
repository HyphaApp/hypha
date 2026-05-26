/**
 * WebAuthn passkey support using native browser APIs.
 *
 * Uses the stable native APIs available in all major browsers since March 2025:
 *   - PublicKeyCredential.parseCreationOptionsFromJSON()
 *   - PublicKeyCredential.parseRequestOptionsFromJSON()
 *   - PublicKeyCredential.prototype.toJSON()
 *
 * Availability is checked via window.PublicKeyCredential && navigator.credentials,
 * which covers platform authenticators (Touch ID, Windows Hello, Face ID) as well
 * as roaming authenticators (security keys) and cross-device auth (QR code).
 */

window.hypha = window.hypha || {};

window.hypha.passkeys = (function () {
  let _conditionalAbortController = null;
  function getCsrfToken() {
    const hxheaders = document.body.getAttribute("hx-headers") || "{}";
    const headers = JSON.parse(hxheaders);
    return headers["X-CSRFToken"] || "";
  }

  function getRememberMe() {
    const el =
      document.getElementById("id_auth-remember_me") ||
      document.getElementById("id_remember_me");
    return el ? el.checked : false;
  }

  function jsonPost(url, body) {
    return fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify(body),
    });
  }

  /**
   * Show passkey-related UI elements only when the platform supports them.
   * Call this on DOMContentLoaded — elements with data-passkey-ui are hidden
   * by default and revealed here.
   */
  async function initUI() {
    const webAuthnAvailable = !!(
      window.PublicKeyCredential && navigator.credentials
    );

    const conditionalOk = await (
      window.PublicKeyCredential?.isConditionalMediationAvailable?.() ??
      Promise.resolve(false)
    ).catch(() => false);

    if (webAuthnAvailable) {
      document
        .querySelectorAll("[data-passkey-ui]")
        .forEach((el) => el.removeAttribute("hidden"));
    }

    if (conditionalOk) {
      _startConditionalMediation();
    }
  }

  /**
   * Register a new passkey for the currently authenticated user.
   * Called from the account page "Add passkey" form (onsubmit).
   * @param {HTMLFormElement} formEl  The <form> element containing a [name=name] input.
   */
  async function register(formEl) {
    const beginUrl = formEl?.dataset.beginUrl;
    const completeUrl = formEl?.dataset.completeUrl;
    if (!beginUrl || !completeUrl) return;

    const nameInput = formEl?.querySelector("[name=name]");
    const errorEl = document.getElementById("passkey-error");
    const submitBtn = formEl?.querySelector("[type=submit]");

    try {
      if (submitBtn) submitBtn.disabled = true;
      if (errorEl) errorEl.hidden = true;

      // Step 1: fetch registration options from server
      const beginResp = await jsonPost(beginUrl, {});
      if (!beginResp.ok) {
        const err = await beginResp.json();
        throw new Error(
          err.error || formEl?.dataset.errorServer || "Server error"
        );
      }
      const options = await beginResp.json();

      // Step 2: trigger native OS passkey creation UI (Touch ID / Windows Hello / …)
      const credential = await navigator.credentials.create({
        publicKey: PublicKeyCredential.parseCreationOptionsFromJSON(options),
      });

      // Step 3: send the signed response to the server
      const completeResp = await jsonPost(completeUrl, {
        ...credential.toJSON(),
        name: nameInput?.value.trim() || "",
      });
      if (!completeResp.ok) {
        const err = await completeResp.json();
        throw new Error(
          err.error || formEl?.dataset.errorRegister || "Registration failed"
        );
      }

      // Reload to show the new passkey in the list
      window.location.reload();
    } catch (err) {
      // NotAllowedError means the user dismissed the native OS dialog — not an error.
      if (err.name === "NotAllowedError") {
        // user cancelled — do nothing
      } else if (err.name === "InvalidStateError") {
        if (errorEl) {
          errorEl.textContent =
            formEl?.dataset.errorDuplicate ||
            "This authenticator already has a passkey registered. Try a different authenticator or device.";
          errorEl.hidden = false;
        }
      } else if (errorEl) {
        errorEl.textContent = err.message;
        errorEl.hidden = false;
      }
    } finally {
      if (submitBtn) submitBtn.disabled = false;
    }
  }

  /**
   * Authenticate with a passkey via an explicit button click on the login page.
   */
  async function authenticate() {
    // Abort any in-progress conditional mediation before starting explicit auth.
    if (_conditionalAbortController) {
      _conditionalAbortController.abort();
      _conditionalAbortController = null;
    }

    const btn = document.getElementById("btn-passkey-login");
    const beginUrl = btn?.dataset.beginUrl;
    const completeUrl = btn?.dataset.completeUrl;
    if (!beginUrl || !completeUrl) return;

    const nextUrl = btn?.dataset.nextUrl || "";
    const errorEl = document.getElementById("passkey-auth-error");

    try {
      const beginResp = await jsonPost(beginUrl, {});
      if (!beginResp.ok)
        throw new Error(
          errorEl?.dataset.errorBegin || "Failed to begin authentication"
        );
      const authOptions = await beginResp.json();

      // Triggers native OS passkey selection UI
      const credential = await navigator.credentials.get({
        publicKey: PublicKeyCredential.parseRequestOptionsFromJSON(authOptions),
      });

      const completeResp = await jsonPost(completeUrl, {
        ...credential.toJSON(),
        next: nextUrl,
        remember_me: getRememberMe(),
      });
      if (!completeResp.ok) {
        const err = await completeResp.json();
        throw new Error(
          err.error || errorEl?.dataset.errorAuth || "Authentication failed"
        );
      }
      const data = await completeResp.json();
      const redirectUrl = new URL(
        data.redirect_url || "/",
        window.location.origin
      );
      window.location.href =
        redirectUrl.origin === window.location.origin
          ? redirectUrl.pathname + redirectUrl.search + redirectUrl.hash
          : "/";
    } catch (err) {
      // NotAllowedError / AbortError = user dismissed the native UI.
      if (err.name !== "NotAllowedError" && err.name !== "AbortError") {
        if (errorEl) {
          errorEl.textContent = err.message;
          errorEl.hidden = false;
        }
      }
    }
  }

  /**
   * Internal: start conditional mediation (passkey autofill on the login page).
   * The email input needs autocomplete="username webauthn" for this to work.
   */
  async function _startConditionalMediation() {
    const btn = document.getElementById("btn-passkey-login");
    const beginUrl = btn?.dataset.beginUrl;
    const completeUrl = btn?.dataset.completeUrl;
    if (!beginUrl || !completeUrl) return;

    _conditionalAbortController = new AbortController();

    try {
      const beginResp = await jsonPost(beginUrl, {});
      if (!beginResp.ok) return;
      const authOptions = await beginResp.json();

      // mediation:"conditional" shows registered passkeys in the browser
      // autofill dropdown next to the email field — no explicit user gesture needed.
      const credential = await navigator.credentials.get({
        publicKey: PublicKeyCredential.parseRequestOptionsFromJSON(authOptions),
        mediation: "conditional",
        signal: _conditionalAbortController.signal,
      });

      if (!credential) return;

      const nextUrl = btn?.dataset.nextUrl || "";
      const completeResp = await jsonPost(completeUrl, {
        ...credential.toJSON(),
        next: nextUrl,
        remember_me: getRememberMe(),
      });
      if (!completeResp.ok) return;
      const data = await completeResp.json();
      const redirectUrl = new URL(
        data.redirect_url || "/",
        window.location.origin
      );
      window.location.href =
        redirectUrl.origin === window.location.origin
          ? redirectUrl.pathname + redirectUrl.search + redirectUrl.hash
          : "/";
    } catch (_err) {
      // Expected: aborted when user submits the password form normally.
    }
  }

  return { initUI, register, authenticate };
})();
