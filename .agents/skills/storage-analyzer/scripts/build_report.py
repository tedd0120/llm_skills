from pathlib import Path
from common import parser, existing_output, SKILL
BASE=existing_output(parser('生成离线 HTML 报告').parse_args())
data=(BASE/'report-data.json').read_text(encoding='utf-8').replace('<','\\u003c')
(BASE/'report.html').write_text((SKILL/'assets/report_template.html').read_text(encoding='utf-8').replace('__REPORT_DATA__',data),encoding='utf-8')
