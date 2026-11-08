import { webview } from '@kit.ArkWeb';
import { hilog } from '@kit.PerformanceAnalysisKit';

const DOMAIN: number = 0x0100;
const TAG: string = 'HistoryScroll';

/*
 * 给 web 侧调用的桥。
 * native-shim.js 里通过 window.harmonyBridge.onViewChange('map') 上报当前视图，
 * 壳据此决定按返回键时「先回长卷」还是「退出应用」。
 */
class NativeBridge {
  private viewCb: (view: string) => void = () => {};

  setViewCallback(cb: (view: string) => void): void {
    this.viewCb = cb;
  }

  onViewChange(view: string): void {
    this.viewCb(view);
  }

  onReady(view: string): void {
    this.viewCb(view);
  }
}

@Entry
@Component
struct Index {
  private controller: webview.WebviewController = new webview.WebviewController();
  private bridge: NativeBridge = new NativeBridge();
  @State currentView: string = 'scroll';
  @State showDiag: boolean = false;
  @State diagText: string = '';

  aboutToAppear(): void {
    this.bridge.setViewCallback((view: string) => {
      this.currentView = view;
    });
    // 25 秒后自检史图是否真的加载出来了（rawfile 下 iframe 是唯一有风险的一环）
    setTimeout(() => {
      this.checkMapHealth();
    }, 25000);
  }

  checkMapHealth(): void {
    const script: string = `
      (function () {
        var f = document.getElementById('map-embed');
        if (!f) return 'no-frame';
        if (!f.getAttribute('src')) return 'no-src';
        try {
          var d = f.contentDocument;
          if (d && d.querySelector('.archive-folder-tab')) return 'ok';
        } catch (e) {
          return 'blocked';
        }
        return 'pending';
      })();
    `;
    this.controller.runJavaScript(script).then((res: string) => {
      if (res !== 'ok') {
        this.diagText = '史图未就绪（' + res + '），长卷功能不受影响';
        this.showDiag = true;
        hilog.warn(DOMAIN, TAG, 'map health: %{public}s', res);
      }
    }).catch((e: Error) => {
      hilog.warn(DOMAIN, TAG, 'checkMapHealth: %{public}s', e.message);
    });
  }

  build() {
    Stack({ alignContent: Alignment.Bottom }) {
      Web({ src: $rawfile('web/index.html'), controller: this.controller })
        .javaScriptAccess(true)
        .domStorageAccess(true)
        .fileAccess(true)
        .imageAccess(true)
        .zoomAccess(false)
        .horizontalScrollBarAccess(false)
        .verticalScrollBarAccess(false)
        .darkMode(WebDarkMode.Off)
        .onErrorReceive((event) => {
          if (event) {
            hilog.error(DOMAIN, TAG, 'web error: %{public}s', event.error.getErrorInfo());
          }
        })
        .javaScriptProxy({
          object: this.bridge,
          name: 'harmonyBridge',
          methodList: ['onViewChange', 'onReady'],
          controller: this.controller
        })
        .width('100%')
        .height('100%')

      if (this.showDiag) {
        Row({ space: 12 }) {
          Text(this.diagText)
            .fontSize(12)
            .fontColor('#FFFFFF')
            .layoutWeight(1)
          Button('关闭')
            .fontSize(12)
            .height(28)
            .backgroundColor('#00000000')
            .fontColor('#FFFFFF')
            .onClick(() => {
              this.showDiag = false;
            })
        }
        .width('90%')
        .padding({ left: 14, right: 8, top: 6, bottom: 6 })
        .backgroundColor('#D93A2F24')
        .borderRadius(8)
        .margin({ bottom: 28 })
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F0E6')
  }

  onBackPress(): boolean {
    if (this.currentView !== 'scroll') {
      this.controller.runJavaScript('window.__nativeBack && window.__nativeBack();');
      return true;
    }
    return false;
  }
}
