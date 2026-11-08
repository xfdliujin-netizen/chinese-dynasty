import Foundation
import WebKit

/// 把 app://local/... 映射到 Bundle 内 web/ 目录的自定义协议处理器。
///
/// 之所以不用 file://：WKWebView 对 file:// 的 iframe 与 localStorage 限制较多；
/// 自定义 scheme 提供稳定 origin（app://local），iframe 同源、字体、存储行为与浏览器一致。
final class AppSchemeHandler: NSObject, WKURLSchemeHandler {
    private let root: URL
    /// WKURLSchemeTask 被取消后再回调会直接崩溃，用标识集合拦住
    private var stopped = Set<ObjectIdentifier>()
    private let lock = NSLock()

    init() {
        let base = Bundle.main.resourceURL ?? Bundle.main.bundleURL
        self.root = base.appendingPathComponent("web", isDirectory: true)
    }

    func webView(_ webView: WKWebView, start task: WKURLSchemeTask) {
        lock.lock()
        let wasStopped = stopped.contains(ObjectIdentifier(task))
        lock.unlock()
        if wasStopped { return }

        guard let url = task.request.url else {
            task.didFailWithError(URLError(.badURL))
            return
        }

        var relPath = url.path
        if relPath.hasPrefix("/") { relPath.removeFirst() }
        if relPath.isEmpty { relPath = "index.html" }
        relPath = relPath.removingPercentEncoding ?? relPath

        let file = root.appendingPathComponent(relPath).standardizedFileURL
        guard file.path.hasPrefix(root.standardizedFileURL.path) else {
            task.didFailWithError(URLError(.fileDoesNotExist))
            return
        }

        guard let data = try? Data(contentsOf: file) else {
            task.didFailWithError(URLError(.fileDoesNotExist))
            return
        }

        lock.lock()
        let cancelled = stopped.contains(ObjectIdentifier(task))
        lock.unlock()
        if cancelled { return }

        let response = URLResponse(
            url: url,
            mimeType: Self.mime(for: relPath),
            expectedContentLength: data.count,
            textEncodingName: Self.isText(mime: Self.mime(for: relPath)) ? "utf-8" : nil
        )
        task.didReceive(response)
        task.didReceive(data)
        task.didFinish()
    }

    func webView(_ webView: WKWebView, stop task: WKURLSchemeTask) {
        lock.lock()
        stopped.insert(ObjectIdentifier(task))
        lock.unlock()
    }

    private static func isText(mime: String) -> Bool {
        mime.hasPrefix("text/") || mime.contains("javascript") || mime.contains("json")
    }

    private static func mime(for path: String) -> String {
        let ext = (path as NSString).pathExtension.lowercased()
        switch ext {
        case "html", "htm": return "text/html"
        case "js", "mjs":   return "application/javascript"
        case "css":         return "text/css"
        case "json":        return "application/json"
        case "webp":        return "image/webp"
        case "png":         return "image/png"
        case "jpg", "jpeg": return "image/jpeg"
        case "gif":         return "image/gif"
        case "svg":         return "image/svg+xml"
        case "woff":        return "font/woff"
        case "woff2":       return "font/woff2"
        case "ttf":         return "font/ttf"
        case "otf":         return "font/otf"
        case "ogg":         return "audio/ogg"
        case "mp3":         return "audio/mpeg"
        default:            return "application/octet-stream"
        }
    }
}
