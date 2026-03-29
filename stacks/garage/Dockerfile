FROM dxflrs/garage:v2.1.0

USER root
COPY garage.toml.tmpl /config/garage.toml.template
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chmod 644 /config/garage.toml.template
USER garage

ENTRYPOINT ["/entrypoint.sh"]
CMD []
