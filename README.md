# Knowledge Exporter

Export your purchased content from paid knowledge providers, supported format including column, video, audio, etc.

#### How to install

pip install knowledge-exporter

#### How to use

```
Usage: knowledge-exporter [OPTIONS] COLUMN_ID

  📑 -> 📚 导出知识付费平台内容

Options:
  -t, --target [GeekTime]         知识付费平台  [required]
  -u, --username TEXT             手机号/用户名  [required]
  -p, --password TEXT             密码  [required]
  --merge / --no-merge            合并专栏文章
  --show-comments / --no-comments
                                  显示文章评论
  --help                          Show this message and exit.
```


#### PS

导出已购买的知识付费产品，包括专栏、视频、音频等。

项目还很早期，欢迎 Issue / Pull Request / Fork。

支持平台：

- [x] 极客时间
- [ ] 慕课网
- [ ] 得到
- [ ] 拉钩教育
- [ ] 其他

支持格式：

- [x] PDF（方便iPad查阅、批注）
- [ ] 视频合集
