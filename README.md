# 实时模拟仿真果冻 skill

基于 WebGPU / Three.js 的实时软体果冻互动工程，支持默认 Jelly Baby 与孙悟空果冻切换。

在线体验：[打开 Vercel 正式版](https://realtime-jelly-simulation-skill.vercel.app)

原预览：[Jelly Lab](https://wukong-jelly-lab.pokemonzangoose.chatgpt.site)

## 功能
- 重力、台面碰撞、拖拽拉伸、抛掷、回弹与体积保持。
- 默认 Jelly Baby 和一体化孙悟空模型；切换无需刷新页面。
- 360° 酒吧 HDR 环境、折射与焦散近似、景深、电影感灯光和石质台面。
- 台面上方半球环绕、缩放、移动端触控及安全区适配。
- 240 Hz XPBD 软体物理，内嵌 WebAssembly 内核，光学计算 Worker。

## 本地运行
使用 Node.js 22.18+，在支持 WebGPU 的浏览器中运行。WebGPU 需要 localhost 或 HTTPS；本工程不提供 WebGL 回退。

```sh
npm ci
npm run dev
```

```sh
npm run build
npm run preview
```

部署时发布 `dist/`，预生成模型和 HDR 已包含，无需重新建模。

## 操作
拖拽果冻拉伸或抛掷；拖拽台面环绕；滚轮或双指缩放。左侧（移动端顶部）切换形象。键盘 WASD / 方向键移动，空格跳跃，R 重置。首次交互启用声音。

## 模型与校验
孙悟空采用隐式曲面生成单一闭合表面，并绑定四面体物理笼及光学代理。当前表面为 139,289 个顶点、278,602 个三角形。

```sh
npm run typecheck
npm run test:physics
node --experimental-strip-types scripts/verify-wukong.mjs
npm run build
```

重新生成孙悟空需要 Python、NumPy、SciPy、scikit-image：
```sh
python -m pip install numpy scipy scikit-image
python scripts/build-wukong-model.py
```

该命令会同时执行雕刻脚本并输出中间曲面及最终运行资源。可选灰模预览另需 matplotlib：
```sh
python -m pip install matplotlib
python scripts/preview-wukong.py
```

## 目录
- `src/game/`：输入、运行生命周期、形象切换、声音。
- `src/physics/`：软体求解、抓取、模型加载。
- `src/graphics/`：果冻材质、折射、焦散、HDR、台面与后处理。
- `src/assets/`：模型、环境与纹理资源（含历史资源）。
- `scripts/`：模型生成、物理验证与性能检查。
- `refs/`：上游参考与 HDR 来源说明。

光学使用屏幕空间透射、简化代理和共享 RGB 光路等实时近似，不是离线路径追踪。最终画质与帧率取决于设备和浏览器 WebGPU 支持。

## 来源
工程基于 [scottstts/Jelly-Baby](https://github.com/scottstts/Jelly-Baby) 扩展，保留其默认果冻与物理/光学实现。上游代码的使用与再分发应以其授权为准，本仓库未为上游代码追加许可证。

Warm Bar HDR 来自 [Poly Haven](https://polyhaven.com/a/warm_bar)，CC0，详见 `refs/warm-bar.md`。

本仓库目前是可运行的 Web 工程；仓库名称中的 skill 不表示已封装为带 SKILL.md 的可安装技能。

## 大文件存储
受上传接口限制，孙悟空模型和历史木纹贴图以 gzip 分块保存在 `packed-assets/`。`npm ci` 会自动无损还原，并校验 SHA-256；禁用安装脚本时请手动执行 `npm run assets:restore`。开发和构建前也会检查还原状态。

## Vercel 部署
正式地址：https://realtime-jelly-simulation-skill.vercel.app

当前发布为预构建的完整静态版本，模型、HDR 和页面资源均托管在 Vercel。暂未建立 GitHub 自动部署关联，后续源码提交需要重新部署。通过 Git 导入时选择 Vite，安装命令 `npm ci`，构建命令 `npm run build`，输出目录 `dist`。
