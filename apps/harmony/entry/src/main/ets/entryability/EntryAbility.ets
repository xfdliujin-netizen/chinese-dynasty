import { AbilityConstant, UIAbility, Want } from '@kit.AbilityKit';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { window } from '@kit.ArkUI';

const DOMAIN: number = 0x0100;
const TAG: string = 'HistoryScroll';

export default class EntryAbility extends UIAbility {
  onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
    hilog.info(DOMAIN, TAG, 'onCreate');
  }

  onDestroy(): void {
    hilog.info(DOMAIN, TAG, 'onDestroy');
  }

  onWindowStageCreate(windowStage: window.WindowStage): void {
    windowStage.loadContent('pages/Index', (err) => {
      if (err.code) {
        hilog.error(DOMAIN, TAG, 'loadContent failed: %{public}s', JSON.stringify(err));
        return;
      }
      try {
        const win: window.Window = windowStage.getMainWindowSync();
        win.setWindowBackgroundColor('#F5F0E6');
        win.setWindowSystemBarProperties({
          statusBarColor: '#F5F0E6',
          statusBarContentColor: '#231D16',
          navigationBarColor: '#F5F0E6',
          navigationBarContentColor: '#231D16'
        }).catch((e: Error) => {
          hilog.warn(DOMAIN, TAG, 'system bar style skipped: %{public}s', e.message);
        });
      } catch (e) {
        hilog.warn(DOMAIN, TAG, 'window style failed');
      }
    });
  }

  onWindowStageDestroy(): void {
    hilog.info(DOMAIN, TAG, 'onWindowStageDestroy');
  }

  onForeground(): void {}

  onBackground(): void {}
}
